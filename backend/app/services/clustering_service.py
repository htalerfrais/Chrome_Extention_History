import logging
from typing import List, Dict, Any, Optional
import json

from app.config import settings
from ..models.session_models import HistorySession, ClusterResult, ClusterItem, SessionClusteringResponse
from ..models.llm_models import LLMRequest
from .llm_service import LLMService

logger = logging.getLogger(__name__)


class ClusteringService:
    """LLM-driven clustering service: identifies clusters and assigns items per session."""

    def __init__(self, mapping_service=None):
        self.llm_service = LLMService()
        self.batch_size = settings.clustering_batch_size
        self.max_tokens = settings.clustering_max_tokens
        self.mapping_service = mapping_service  # Injected for caching and persistence

    async def cluster_session(self, session: HistorySession, user_id: int) -> SessionClusteringResponse:
        """
        Cluster session with caching and automatic persistence
        
        1. Check if session already analyzed for this user
        2. If cached, return existing result from DB
        3. If not, run LLM clustering
        4. Save result to DB
        5. Return result
        """
        logger.info(f"📊 Processing session {session.session_identifier} with {len(session.items)} items")
        
        # Step 1: Check if session already analyzed (cache check)
        if self.mapping_service:
            cached_result = self.mapping_service.get_clustering_result(session.session_identifier)
            if cached_result:
                logger.info(f"✅ Found cached result for session {session.session_identifier}, returning without LLM calls")
                return cached_result
            logger.info(f"🆕 No cached result found, proceeding with LLM clustering")

        # Step 1: Ask LLM to propose clusters for this session
        clusters_meta = await self.identify_clusters_for_session(session)

        # Step 2: Assign each item to one of the identified clusters
        cluster_id_to_items = await self.assign_items_to_clusters(session, clusters_meta)

        # Build ClusterResult objects
        cluster_results: List[ClusterResult] = []
        for meta in clusters_meta:
            cluster_id: str = meta.get("cluster_id") or f"cluster_{session.session_identifier}_{len(cluster_results)}"
            theme: str = meta.get("theme") or "Miscellaneous"
            summary: str = meta.get("summary") or ""

            items = cluster_id_to_items.get(cluster_id, [])
            if len(items) == 0:
                # Skip empty clusters to keep output compact
                continue

            cluster_results.append(ClusterResult(
                cluster_id=cluster_id,
                theme=theme,
                summary=summary,
                items=items
            ))

        # Create session response
        response = SessionClusteringResponse(
            session_identifier=session.session_identifier,
            session_start_time=session.start_time,
            session_end_time=session.end_time,
            clusters=cluster_results
        )

        # Log ClusterResult models
        for cluster_result in cluster_results:
            logger.info(f"🎯 ClusterResult: {cluster_result.model_dump()}")
        
        # Step 3: Save to database (automatic persistence)
        if self.mapping_service:
            try:
                session_id = self.mapping_service.save_clustering_result(user_id, response)
                logger.info(f"💾 Saved clustering result to database with session_id: {session_id}")
            except Exception as e:
                logger.error(f"❌ Failed to save clustering result to database: {e}")
                # Don't fail the request, just log the error

        return response

    async def identify_clusters_for_session(self, session: HistorySession) -> List[Dict[str, Any]]:
        """Use LLM to propose clusters (cluster_id, theme, summary) for a session."""
        simplified_items = self._prepare_session_items_for_llm(session)

        example = [
            {
                "cluster_id": "cluster_1",
                "theme": "Web Development",
                "summary": "Extensive exploration of coding resources including GitHub repositories for React projects, Stack Overflow discussions about API integration, and documentation for modern web frameworks. Focus on frontend development tools and debugging techniques."
            },
            {
                "cluster_id": "cluster_2",
                "theme": "Research & Learning",
                "summary": "In-depth research session covering tutorials on machine learning algorithms, academic papers about neural networks, and educational videos explaining complex programming concepts. Multiple visits to documentation sites and learning platforms."
            },
            {
                "cluster_id": "cluster_generic",
                "theme": "General Browsing",
                "summary": "Miscellaneous browsing activity including social media checks, news articles, and various unrelated pages that don't form a cohesive theme."
            }
        ]

        prompt = (
            "You are an assistant that organizes web browsing sessions into thematic clusters.\n"
            "Given the simplified list of session items, identify between 1 and 10 THEMATIC clusters.\n"
            "IMPORTANT: You must ALWAYS include a 'cluster_generic' cluster for items that don't fit specific themes.\n\n"
            "For each cluster, provide:\n"
            "- A clear, descriptive theme name\n"
            "- A DETAILED summary (2-3 sentences) that:\n"
            "  * Describes the main activities and topics explored\n"
            "  * Mentions specific websites or types of content visited\n"
            "  * Explains the user's apparent goal or interest\n"
            "  * Uses engaging, informative language\n\n"
            "Return ONLY a compact JSON array. Each element must have keys: \"cluster_id\", \"theme\", \"summary\".\n"
            "Do not include any other text.\n\n"
            f"Example format:\n{json.dumps(example, ensure_ascii=False)}\n\n"
            f"Session items (simplified):\n{json.dumps(simplified_items, ensure_ascii=False)}\n"
        )

        try:
            req = LLMRequest(prompt=prompt, provider=settings.default_provider, max_tokens=self.max_tokens, temperature=settings.clustering_temperature)
            resp = await self.llm_service.generate_text(req)
            raw = resp.generated_text.strip()
            
            data = self._extract_json(raw)
            if isinstance(data, list):
                # Basic schema cleanup
                cleaned: List[Dict[str, Any]] = []
                has_generic = False
                
                for idx, c in enumerate(data):
                    if not isinstance(c, dict):
                        continue
                    cid = str(c.get("cluster_id") or f"cluster_{idx+1}")
                    theme = str(c.get("theme") or "Miscellaneous")
                    summary = str(c.get("summary") or "")
                    
                    # Track if generic cluster is present
                    if cid == "cluster_generic":
                        has_generic = True
                    
                    cleaned.append({"cluster_id": cid, "theme": theme, "summary": summary})
                
                # ALWAYS ensure generic cluster exists
                if not has_generic:
                    cleaned.append({
                        "cluster_id": "cluster_generic",
                        "theme": "General Browsing",
                        "summary": "General browsing activity that doesn't fit into specific thematic clusters"
                    })
                
                if cleaned:
                    return cleaned
        except Exception as e:
            logger.error(f"LLM cluster identification failed for session {session.session_identifier}: {e}")

        # Fallback: single generic cluster
        return [{
            "cluster_id": "cluster_generic",
            "theme": "General Browsing",
            "summary": "General browsing activity that doesn't fit into specific thematic clusters"
        }]

    async def assign_items_to_clusters(self, session: HistorySession, clusters_meta: List[Dict[str, Any]]) -> Dict[str, List[ClusterItem]]:
        """Assign items in batches to reduce the number of LLM calls."""
        cluster_map: Dict[str, List[ClusterItem]] = {c["cluster_id"]: [] for c in clusters_meta}
        valid_ids = {c["cluster_id"] for c in clusters_meta}

        BATCH_SIZE = self.batch_size  # be careful with this value, Gemini 2.5-Pro inconsistent MAX_TOKENS behavior because of internal reasoning tokens
        items = session.items
        for start in range(0, len(items), BATCH_SIZE):
            batch = items[start:start + BATCH_SIZE]
            logger.info(f"📦 Processing batch with {len(batch)} items")
            assigned_ids = await self._assign_batch_to_clusters(batch, clusters_meta)

            # Safety: ensure alignment
            if len(assigned_ids) != len(batch):
                first_cluster = next(iter(valid_ids)) if valid_ids else "cluster_generic"
                assigned_ids = [first_cluster] * len(batch)

            for item, assigned_id in zip(batch, assigned_ids):
                if assigned_id not in valid_ids:
                    assigned_id = next(iter(valid_ids)) if valid_ids else "cluster_generic"

                cluster_item = ClusterItem(
                    url=item.url,
                    title=item.title,
                    visit_time=item.visit_time,
                    url_hostname=item.url_hostname,
                    url_pathname_clean=item.url_pathname_clean,
                    url_search_query=item.url_search_query
                )
                cluster_map[assigned_id].append(cluster_item)

        return cluster_map

    async def _assign_batch_to_clusters(self, items_batch: List[Any], clusters_meta: List[Dict[str, Any]]) -> List[str]:
        """Assign a batch of items to clusters with a single LLM call. Returns a list of cluster_ids."""
        clusters_json = json.dumps(clusters_meta, ensure_ascii=False)
        simplified_batch = [self._simplify_item_for_llm(item) for item in items_batch]

        prompt = (
            "You are assigning browsing items to predefined clusters.\n"
            "IMPORTANT: Use 'cluster_generic' for items that don't clearly fit any specific thematic cluster.\n"
            "Only assign items to thematic clusters if they clearly belong to that theme.\n"
            "When in doubt, use 'cluster_generic'.\n\n"
            "Return ONLY a JSON array of cluster_id strings, one for each item in order.\n\n"
            f"Clusters:\n{clusters_json}\n\n"
            f"Items to assign (in order):\n{json.dumps(simplified_batch, ensure_ascii=False)}\n\n"
            "Return format example: [\"cluster_1\", \"cluster_generic\", \"cluster_2\"]\n"
        )

        try:
            req = LLMRequest(prompt=prompt, provider=settings.default_provider, max_tokens=self.max_tokens, temperature=0.0)
            resp = await self.llm_service.generate_text(req)
            raw = resp.generated_text.strip()
            
            assignments = self._extract_json(raw)
            # Expecting a list of strings
            if isinstance(assignments, list) and all(isinstance(x, (str,)) for x in assignments):
                return [str(x).strip() for x in assignments]
        except Exception as e:
            logger.warning(f"Batch assignment failed: {e}")

        # Fallback: assign everything to the first cluster (if any)
        first_cluster = clusters_meta[0]["cluster_id"] if clusters_meta else "cluster_generic"
        return [first_cluster] * len(items_batch)




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


