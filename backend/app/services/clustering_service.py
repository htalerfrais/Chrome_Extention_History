import logging
import time
from typing import List, Dict, Any, Optional
import json

import numpy as np

from app.config import settings
from ..models.session_models import HistorySession, ClusterResult, ClusterItem, SessionClusteringResponse, SemanticGroup
from ..models.llm_models import LLMRequest
from .llm_service import LLMService
from .embedding_service import EmbeddingService
from ..monitoring import track_performance, get_request_id, metrics, calculate_llm_cost

logger = logging.getLogger(__name__)

# Hardcoded fallback cluster for items that don't match any thematic cluster
GENERIC_CLUSTER = {
    "cluster_id": "cluster_generic",
    "theme": "General Browsing",
    "summary": "Miscellaneous browsing activity that doesn't fit into specific thematic clusters."
}


def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(vec_a)
    b = np.array(vec_b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


class ClusteringService:
    def __init__(self, mapping_service=None, embedding_service: Optional[EmbeddingService] = None):
        self.llm_service = LLMService()
        self.max_tokens = settings.clustering_max_tokens
        self.mapping_service = mapping_service
        self.embedding_service = embedding_service or EmbeddingService()

    @track_performance(operation="clustering")
    async def cluster_session(self, session: HistorySession, user_id: int, force: bool = False) -> SessionClusteringResponse:
        session.session_identifier = f"u{user_id}:{session.session_identifier}"
        
        # Step 1: Check cache
        cache_hit = False
        if self.mapping_service and not force:
            cached_result = self.mapping_service.get_clustering_result(session.session_identifier)
            if cached_result:
                cache_hit = True
                logger.info(
                    "clustering_cache_check",
                    extra={
                        "request_id": get_request_id(),
                        "session_id": session.session_identifier,
                        "force": force,
                        "cache_hit": True
                    }
                )
                # Record cache hit
                metrics.record_clustering(cached=True, groups=0, clusters=len(cached_result.clusters), duration_ms=0)
                return cached_result
        
        logger.info(
            "clustering_cache_check",
            extra={
                "request_id": get_request_id(),
                "session_id": session.session_identifier,
                "force": force,
                "cache_hit": False
            }
        )

        # Step 2: Create semantic groups
        groups = self._create_semantic_groups(session)
        compression_ratio = len(session.items) / len(groups) if groups else 0
        
        logger.info(
            "clustering_groups_created",
            extra={
                "request_id": get_request_id(),
                "session_id": session.session_identifier,
                "input_items": len(session.items),
                "output_groups": len(groups),
                "compression_ratio": round(compression_ratio, 2),
                "groups_sample": [
                    {"title": g.title, "hostname": g.hostname, "item_count": g.item_count}
                    for g in groups[:5]
                ]
            }
        )

        # Step 3: Embed groups
        groups = await self._embed_semantic_groups(groups)
        
        # Step 4: LLM cluster identification
        llm_start = time.perf_counter()
        clusters_meta = await self.identify_clusters_from_groups(groups)
        llm_duration_ms = (time.perf_counter() - llm_start) * 1000
        
        logger.info(
            "clustering_llm_identified",
            extra={
                "request_id": get_request_id(),
                "session_id": session.session_identifier,
                "clusters_identified": len(clusters_meta),
                "duration_ms": round(llm_duration_ms, 2),
                "cluster_themes": [c.get("theme") for c in clusters_meta],
                "clusters_detail": clusters_meta
            }
        )

        # Step 5: Embed clusters
        clusters_meta = await self._embed_clusters(clusters_meta)

        # Step 6: Assign groups to clusters
        cluster_id_to_groups = self._assign_groups_by_similarity(groups, clusters_meta)
        
        # Calculate assignment distribution
        assignment_distribution = {
            cluster_id: len(groups_list)
            for cluster_id, groups_list in cluster_id_to_groups.items()
        }
        generic_count = len(cluster_id_to_groups.get(GENERIC_CLUSTER["cluster_id"], []))
        generic_percentage = (generic_count / len(groups) * 100) if groups else 0
        
        logger.info(
            "clustering_assignment_complete",
            extra={
                "request_id": get_request_id(),
                "session_id": session.session_identifier,
                "assignment_distribution": assignment_distribution,
                "generic_cluster_count": generic_count,
                "generic_percentage": round(generic_percentage, 2)
            }
        )

        # Step 7: Decompress groups to items
        cluster_id_to_items = self._decompress_groups_to_items(cluster_id_to_groups)

        cluster_results: List[ClusterResult] = []
        
        # Add thematic clusters from LLM
        for meta in clusters_meta:
            cluster_id: str = meta.get("cluster_id") or f"cluster_{len(cluster_results)}"
            theme: str = meta.get("theme") or "Miscellaneous"
            summary: str = meta.get("summary") or ""
            embedding = meta.get("embedding")

            items = cluster_id_to_items.get(cluster_id, [])
            if len(items) == 0:
                # Skip empty clusters
                continue

            cluster_results.append(ClusterResult(
                cluster_id=cluster_id,
                theme=theme,
                summary=summary,
                items=items,
                embedding=embedding if embedding else None
            ))

        generic_items = cluster_id_to_items.get(GENERIC_CLUSTER["cluster_id"], [])
        if generic_items:
            # Embed the generic cluster
            generic_embedding = None
            if self.embedding_service:
                generic_text = self._build_cluster_meta_embedding_text(GENERIC_CLUSTER)
                vectors = await self.embedding_service.embed_texts([generic_text])
                generic_embedding = vectors[0] if vectors and vectors[0] else None
            
            cluster_results.append(ClusterResult(
                cluster_id=GENERIC_CLUSTER["cluster_id"],
                theme=GENERIC_CLUSTER["theme"],
                summary=GENERIC_CLUSTER["summary"],
                items=generic_items,
                embedding=generic_embedding
            ))

        response = SessionClusteringResponse(
            session_identifier=session.session_identifier,
            session_start_time=session.start_time,
            session_end_time=session.end_time,
            clusters=cluster_results
        )

        # Log final result
        logger.info(
            "clustering_complete",
            extra={
                "request_id": get_request_id(),
                "session_id": session.session_identifier,
                "final_clusters": len(cluster_results),
                "total_items": sum(len(c.items) for c in cluster_results),
                "clusters_summary": [
                    {
                        "id": c.cluster_id,
                        "theme": c.theme,
                        "items_count": len(c.items),
                        "has_embedding": c.embedding is not None
                    }
                    for c in cluster_results
                ]
            }
        )
        
        # Step 9: Save to database
        saved_to_db = False
        if self.mapping_service:
            try:
                session_id = self.mapping_service.save_clustering_result(user_id, response, replace_if_exists=force)
                saved_to_db = True
            except Exception as e:
                logger.error(
                    "clustering_save_failed",
                    extra={
                        "request_id": get_request_id(),
                        "session_id": session.session_identifier,
                        "error": str(e)
                    }
                )
        
        # Record to metrics (note: duration is tracked by @track_performance decorator)
        # We'll use 0 as placeholder since decorator handles timing
        metrics.record_clustering(
            cached=False,
            groups=len(groups),
            clusters=len(cluster_results),
            duration_ms=0  # Tracked by decorator
        )

        return response

    def _build_group_embedding_text(self, group: SemanticGroup) -> Optional[str]:
        """Build natural-language embedding text from a SemanticGroup.
        
        Collects all unique search queries and pathnames from items in the group
        to produce a richer text than title+hostname alone.
        """
        title = (group.title or "").strip()
        hostname = (group.hostname or "").strip()

        if not title and not hostname:
            return None

        # Collect unique non-empty search queries from all items
        search_queries: List[str] = []
        seen_queries: set = set()
        for item in group.items:
            q = (item.url_search_query or "").strip()
            if q and q not in seen_queries:
                seen_queries.add(q)
                search_queries.append(q)

        # Collect unique non-trivial pathnames from all items (skip bare "/")
        pathnames: List[str] = []
        seen_paths: set = set()
        for item in group.items:
            p = (item.url_pathname_clean or "").strip()
            if p and p != "/" and p not in seen_paths:
                seen_paths.add(p)
                pathnames.append(p)

        # Build natural-language text
        text = title if title else hostname
        if title and hostname:
            text = f"{title} on {hostname}"

        if pathnames:
            text += f", pages: {', '.join(pathnames)}"

        if search_queries:
            text += f". Searched: {', '.join(search_queries)}"

        return text.strip()[:1200]

    def _build_cluster_meta_embedding_text(self, cluster_meta: Dict[str, Any]) -> str:
        """Build embedding text from cluster metadata (theme + summary)."""
        theme = cluster_meta.get("theme", "")
        summary = cluster_meta.get("summary", "")
        text = f"{theme} - {summary}" if summary else theme
        return text.strip()[:1200]

    def _create_semantic_groups(self, session: HistorySession) -> List[SemanticGroup]:
        groups_dict: Dict[str, List] = {}
        no_title_counter = 0
        
        for item in session.items:
            title = item.title.strip() if item.title else ""
            hostname = item.url_hostname or ""
            
            if not title:
                group_key = f"__notitle__{no_title_counter}::{hostname}"
                no_title_counter += 1
            else:
                group_key = f"{title}::{hostname}"
            
            if group_key not in groups_dict:
                groups_dict[group_key] = []
            groups_dict[group_key].append(item)
        
        # Convert to SemanticGroup objects
        semantic_groups: List[SemanticGroup] = []
        for group_key, items in groups_dict.items():
            # Use first item as representative example
            first_item = items[0]
            title = first_item.title.strip() if first_item.title else ""
            hostname = first_item.url_hostname or ""
            
            semantic_groups.append(SemanticGroup(
                group_key=group_key,
                title=title,
                hostname=hostname,
                item_count=len(items),
                example_visit_time=first_item.visit_time,
                example_pathname_clean=first_item.url_pathname_clean,
                items=items,
                embedding=None
            ))
        
        return semantic_groups

    async def _embed_semantic_groups(self, groups: List[SemanticGroup]) -> List[SemanticGroup]:
        """
        Embed each SemanticGroup once using natural-language text built from
        title, hostname, all unique pathnames, and all unique search queries.
        Returns groups with embedding field populated.
        """
        if not self.embedding_service or not groups:
            return groups

        # Build embedding text for each group
        group_texts: List[str] = []
        group_indices: List[int] = []
        
        for idx, group in enumerate(groups):
            text = self._build_group_embedding_text(group)
            if text:
                group_texts.append(text)
                group_indices.append(idx)

        if not group_texts:
            logger.warning("No valid group texts to embed")
            return groups

        logger.info(f"🔢 Embedding {len(group_texts)} semantic groups")
        vectors = await self.embedding_service.embed_texts(group_texts)
        logger.info(f"✅ Received {len(vectors)} group embeddings")

        # Assign embeddings to groups
        for idx, vector in zip(group_indices, vectors):
            groups[idx].embedding = vector if vector else None

        return groups

    async def _embed_clusters(self, clusters_meta: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not self.embedding_service or not clusters_meta:
            return clusters_meta

        cluster_texts = [self._build_cluster_meta_embedding_text(c) for c in clusters_meta]
        
        logger.info(f"🔢 Embedding {len(cluster_texts)} clusters")
        vectors = await self.embedding_service.embed_texts(cluster_texts)
        logger.info(f"✅ Received {len(vectors)} cluster embeddings")

        # Add embeddings to cluster metadata
        for cluster, vector in zip(clusters_meta, vectors):
            cluster["embedding"] = vector if vector else []

        return clusters_meta

    def _assign_groups_by_similarity(
        self,
        groups: List[SemanticGroup],
        clusters_with_embeddings: List[Dict[str, Any]]
    ) -> Dict[str, List[SemanticGroup]]:
        threshold = settings.clustering_similarity_threshold
        
        # Initialize cluster map (including generic cluster)
        cluster_map: Dict[str, List[SemanticGroup]] = {
            c["cluster_id"]: [] for c in clusters_with_embeddings
        }
        cluster_map[GENERIC_CLUSTER["cluster_id"]] = []
        
        # Filter out clusters without valid embeddings
        valid_clusters = [
            c for c in clusters_with_embeddings 
            if c.get("embedding") and len(c["embedding"]) > 0
        ]
        
        for group in groups:
            group_embedding = group.embedding
            
            if not group_embedding:
                cluster_map[GENERIC_CLUSTER["cluster_id"]].append(group)
                continue
            
            # Find the most similar cluster
            best_cluster_id = GENERIC_CLUSTER["cluster_id"]
            best_similarity = -1.0
            
            for cluster in valid_clusters:
                cluster_embedding = cluster["embedding"]
                similarity = _cosine_similarity(group_embedding, cluster_embedding)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_cluster_id = cluster["cluster_id"]
            
            if best_similarity >= threshold:
                cluster_map[best_cluster_id].append(group)
                logger.debug(f"Group '{group.title[:30]}...' ({group.item_count} items) assigned to '{best_cluster_id}' (similarity: {best_similarity:.3f})")
            else:
                cluster_map[GENERIC_CLUSTER["cluster_id"]].append(group)
                logger.debug(f"Group '{group.title[:30]}...' assigned to generic (best similarity: {best_similarity:.3f} < {threshold})")
        
        return cluster_map

    def _decompress_groups_to_items(
        self,
        cluster_id_to_groups: Dict[str, List[SemanticGroup]]
    ) -> Dict[str, List[ClusterItem]]:
        """
        Expand SemanticGroups back to individual ClusterItems.
        Each item in a group receives the group's embedding.
        
        Args:
            cluster_id_to_groups: Dict mapping cluster_id to list of SemanticGroups
        
        Returns:
            Dict mapping cluster_id to list of ClusterItems
        """
        cluster_id_to_items: Dict[str, List[ClusterItem]] = {}
        
        for cluster_id, groups in cluster_id_to_groups.items():
            items: List[ClusterItem] = []
            
            for group in groups:
                group_embedding = group.embedding
                
                for history_item in group.items:
                    cluster_item = ClusterItem(
                        url=history_item.url,
                        title=history_item.title,
                        visit_time=history_item.visit_time,
                        url_hostname=history_item.url_hostname,
                        url_pathname_clean=history_item.url_pathname_clean,
                        url_search_query=history_item.url_search_query,
                        embedding=group_embedding
                    )
                    items.append(cluster_item)
            
            cluster_id_to_items[cluster_id] = items
        
        return cluster_id_to_items

    async def identify_clusters_from_groups(self, groups: List[SemanticGroup]) -> List[Dict[str, Any]]:
        simplified_groups = self._prepare_groups_for_llm(groups)

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
            }
        ]

        prompt = (
            "You are an assistant that organizes web browsing sessions into thematic clusters.\n"
            "Given the list of browsing activity groups (each group represents pages with the same title on a domain), "
            "identify between 1 and 10 THEMATIC clusters.\n\n"
            "IMPORTANT GUIDELINES:\n"
            "- Create SPECIFIC, semantically distinct clusters. It's better to have more specific clusters than fewer broad ones.\n"
            "- Each cluster should represent a clear, coherent theme that genuinely matches the groups it will contain.\n"
            "- Clusters should be well-separated semantically - avoid creating clusters that are too broad or vague.\n"
            "- If groups represent different specific topics or activities, create separate clusters for them rather than forcing them into a single broad cluster.\n"
            "- Consider creating clusters even for smaller groups if they represent distinct themes that don't fit well into other clusters.\n"
            "- Groups that don't fit any thematic cluster will be handled separately, so prioritize precision over coverage.\n\n"
            "For each cluster, provide:\n"
            "- A clear, descriptive theme name (be specific, not generic)\n"
            "- A DETAILED summary (2-3 sentences) that:\n"
            "  * Describes the main activities and topics explored with precision\n"
            "  * Mentions specific websites or types of content visited\n"
            "  * Explains the user's apparent goal or interest\n"
            "  * Uses engaging, informative language\n"
            "  * Clearly distinguishes this cluster from others\n\n"
            "Return ONLY a compact JSON array. Each element must have keys: \"cluster_id\", \"theme\", \"summary\".\n"
            "Do not include any other text.\n\n"
            f"Example format:\n{json.dumps(example, ensure_ascii=False)}\n\n"
            f"Browsing activity groups:\n{json.dumps(simplified_groups, ensure_ascii=False)}\n"
        )

        try:
            req = LLMRequest(prompt=prompt, provider=settings.default_provider, max_tokens=self.max_tokens, temperature=settings.clustering_temperature)
            resp = await self.llm_service.generate_text(req)
            raw = resp.generated_text.strip()
            
            data = self._extract_json(raw)
            if isinstance(data, list):
                cleaned: List[Dict[str, Any]] = []
                
                for idx, c in enumerate(data):
                    if not isinstance(c, dict):
                        continue
                    cid = str(c.get("cluster_id") or f"cluster_{idx+1}")
                    theme = str(c.get("theme") or "Miscellaneous")
                    summary = str(c.get("summary") or "")
                    
                    if cid == "cluster_generic":
                        continue
                    
                    cleaned.append({"cluster_id": cid, "theme": theme, "summary": summary})
                
                return cleaned
        except Exception as e:
            logger.error(f"LLM cluster identification from groups failed: {e}")

        # Fallback: empty list (all groups will go to hardcoded generic cluster)
        return []

    def _prepare_groups_for_llm(self, groups: List[SemanticGroup]) -> List[Dict[str, Any]]:
        """Return compressed group info for LLM: title, hostname."""
        return [
            {
                "title": g.title,
                "hostname": g.hostname,
            }
            for g in groups
        ]

    def _extract_json(self, text: str) -> Any:
        text = text.strip()
        try:
            return json.loads(text)
        except Exception:
            pass
        # Try to locate first '[' or '{' and last matching bracket
        start_idx = min([i for i in [text.find('['), text.find('{')] if i != -1] or [-1])
        if start_idx == -1:
            raise ValueError("No JSON start found in LLM response")
        end_idx = max(text.rfind(']'), text.rfind('}'))
        if end_idx == -1 or end_idx <= start_idx:
            raise ValueError("No JSON end found in LLM response")
        snippet = text[start_idx:end_idx+1]
        return json.loads(snippet)


