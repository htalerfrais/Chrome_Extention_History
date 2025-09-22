import logging
from typing import List, Dict, Any
import json

from ..models.session_models import HistorySession, ClusterResult, ClusterItem, SessionClusteringResponse
from ..models.llm_models import LLMRequest
from .llm_service import LLMService

logger = logging.getLogger(__name__)

class ClusteringService:
    """LLM-driven clustering service: identifies clusters and assigns items per session."""

    def __init__(self):
        self.llm_service = LLMService()

    async def cluster_sessions(self, sessions: List[HistorySession]) -> Dict[str, SessionClusteringResponse]:
        """
        For each session: identify clusters with summaries using the LLM, then
        assign each item to one of those clusters. Returns a mapping of
        session_id to SessionClusteringResponse.
        """
        logger.info(f"🚀 Starting LLM clustering for {len(sessions)} sessions")

        results: Dict[str, SessionClusteringResponse] = {}

        for session_idx, session in enumerate(sessions, 1):
            logger.info(f"📊 Processing session {session_idx}/{len(sessions)}: {session.session_id} with {len(session.items)} items")

            # Step 1: Ask LLM to propose clusters for this session
            logger.info(f"🔍 Step 1: Identifying clusters for session {session.session_id}")
            clusters_meta = await self._identify_clusters_for_session(session)
            logger.info(f"✅ Step 1 complete: Found {len(clusters_meta)} clusters for session {session.session_id}")

            # Step 2: Assign each item to one of the identified clusters
            logger.info(f"🎯 Step 2: Assigning {len(session.items)} items to clusters for session {session.session_id}")
            cluster_id_to_items = await self._assign_items_to_clusters(session, clusters_meta)
            logger.info(f"✅ Step 2 complete: Items assigned to clusters for session {session.session_id}")

            # Build ClusterResult objects
            logger.info(f"🏗️ Building cluster results for session {session.session_id}")
            cluster_results: List[ClusterResult] = []
            for meta in clusters_meta:
                cluster_id: str = meta.get("cluster_id") or f"cluster_{session.session_id}_{len(cluster_results)}"
                theme: str = meta.get("theme") or "Miscellaneous"
                summary: str = meta.get("summary") or ""

                items = cluster_id_to_items.get(cluster_id, [])
                if len(items) == 0:
                    logger.debug(f"⏭️ Skipping empty cluster {cluster_id} for session {session.session_id}")
                    continue

                cluster_results.append(ClusterResult(
                    cluster_id=cluster_id,
                    theme=theme,
                    summary=summary,
                    items=items
                ))
                logger.debug(f"📦 Created cluster '{theme}' with {len(items)} items")

            # Create session response
            response = SessionClusteringResponse(
                session_id=session.session_id,
                session_start_time=session.start_time,
                session_end_time=session.end_time,
                clusters=cluster_results
            )

            results[session.session_id] = response
            logger.info(f"✅ Session {session.session_id} complete: {len(cluster_results)} clusters generated")

        logger.info(f"🎉 LLM clustering complete! Generated results for {len(results)} sessions")
        return results

    async def _identify_clusters_for_session(self, session: HistorySession) -> List[Dict[str, Any]]:
        """Use LLM to propose clusters (cluster_id, theme, summary) for a session."""
        simplified_items = self._prepare_session_items_for_llm(session)

        example = [
            {
                "cluster_id": "cluster_1",
                "theme": "Web Development",
                "summary": "Pages related to coding, GitHub repositories, and development tools"
            },
            {
                "cluster_id": "cluster_2",
                "theme": "Research",
                "summary": "Documentation, tutorials, and learning resources"
            }
        ]

        prompt = (
            "You are an assistant that organizes web browsing sessions into thematic clusters.\n"
            "Given the simplified list of session items, identify between 3 and 8 clusters.\n"
            "Return ONLY a compact JSON array. Each element must have keys: \"cluster_id\", \"theme\", \"summary\".\n"
            "Do not include any other text.\n\n"
            f"Example format:\n{json.dumps(example, ensure_ascii=False)}\n\n"
            f"Session items (simplified):\n{json.dumps(simplified_items, ensure_ascii=False)}\n"
        )

        try:
            req = LLMRequest(prompt=prompt, provider="google", max_tokens=800, temperature=0.2)
            resp = await self.llm_service.generate_text(req)
            raw = resp.generated_text.strip()
            data = self._extract_json(raw)
            if isinstance(data, list):
                # Basic schema cleanup
                cleaned: List[Dict[str, Any]] = []
                for idx, c in enumerate(data):
                    if not isinstance(c, dict):
                        continue
                    cid = str(c.get("cluster_id") or f"cluster_{idx+1}")
                    theme = str(c.get("theme") or "Miscellaneous")
                    summary = str(c.get("summary") or "")
                    cleaned.append({"cluster_id": cid, "theme": theme, "summary": summary})
                if cleaned:
                    return cleaned
        except Exception as e:
            logger.error(f"LLM cluster identification failed for session {session.session_id}: {e}")

        # Fallback: single generic cluster
        return [{
            "cluster_id": "cluster_generic",
            "theme": "General",
            "summary": "General browsing activity"
        }]

    async def _assign_items_to_clusters(self, session: HistorySession, clusters_meta: List[Dict[str, Any]]) -> Dict[str, List[ClusterItem]]:
        """Assign each item to one of the identified clusters using the LLM."""
        cluster_map: Dict[str, List[ClusterItem]] = {c["cluster_id"]: [] for c in clusters_meta}

        clusters_json = json.dumps(clusters_meta, ensure_ascii=False)
        valid_ids = {c["cluster_id"] for c in clusters_meta}

        for item in session.items:
            simplified_item = self._simplify_item_for_llm(item)

            prompt = (
                "You are assigning a single browsing item to one of the predefined clusters.\n"
                "Return ONLY the \"cluster_id\" string of the best matching cluster from the provided list.\n"
                "If uncertain, choose the closest reasonable cluster. Do not add quotes or extra text.\n\n"
                f"Clusters:\n{clusters_json}\n\n"
                f"Item:\n{json.dumps(simplified_item, ensure_ascii=False)}\n"
            )

            assigned_id: str = None
            try:
                req = LLMRequest(prompt=prompt, provider="google", max_tokens=16, temperature=0.0)
                resp = await self.llm_service.generate_text(req)
                raw = resp.generated_text.strip()
                # Normalize potential quotes / code fences
                raw = raw.strip().strip('`').strip()
                # If response is JSON like {"cluster_id": "..."}
                try:
                    obj = self._extract_json(raw)
                    if isinstance(obj, dict) and "cluster_id" in obj:
                        assigned_id = str(obj["cluster_id"]).strip()
                except Exception:
                    pass
                if not assigned_id:
                    assigned_id = raw.split()[0]
            except Exception as e:
                logger.warning(f"LLM assignment failed for item {getattr(item, 'id', 'unknown')}: {e}")

            if assigned_id not in valid_ids:
                # Fallback: assign to the first cluster
                assigned_id = next(iter(valid_ids))

            cluster_item = ClusterItem(
                id=item.id,
                url=item.url,
                title=item.title,
                visit_time=item.visit_time,
                session_id=session.session_id,
                url_hostname=item.url_hostname,
                url_pathname_clean=item.url_pathname_clean,
                url_search_query=item.url_search_query
            )
            cluster_map[assigned_id].append(cluster_item)

        return cluster_map

    def _prepare_session_items_for_llm(self, session: HistorySession) -> List[Dict[str, Any]]:
        """Return simplified items for prompts: only title, url_hostname, url_pathname_clean, url_search_query."""
        return [
            {
                "title": it.title,
                "url_hostname": it.url_hostname,
                "url_pathname_clean": it.url_pathname_clean,
                "url_search_query": it.url_search_query,
            }
            for it in session.items
        ]

    def _simplify_item_for_llm(self, item: Any) -> Dict[str, Any]:
        """Simplified representation of a single HistoryItem for assignment prompts."""
        return {
            "title": item.title,
            "url_hostname": item.url_hostname,
            "url_pathname_clean": item.url_pathname_clean,
            "url_search_query": item.url_search_query,
        }

    def _extract_json(self, text: str) -> Any:
        """Extract JSON array/object from raw LLM text output."""
        text = text.strip()
        # Direct parse
        try:
            return json.loads(text)
        except Exception:
            pass
        # Try to locate first '[' or '{' and last matching bracket
        start_idx = min([i for i in [text.find('['), text.find('{')] if i != -1] or [-1])
        if start_idx == -1:
            raise ValueError("No JSON start found in LLM response")
        # Heuristic: find last closing bracket
        end_idx = max(text.rfind(']'), text.rfind('}'))
        if end_idx == -1 or end_idx <= start_idx:
            raise ValueError("No JSON end found in LLM response")
        snippet = text[start_idx:end_idx+1]
        return json.loads(snippet)


