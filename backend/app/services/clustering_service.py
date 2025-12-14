import logging
from typing import List, Dict, Any, Optional
import json

import numpy as np

from app.config import settings
from ..models.session_models import HistorySession, ClusterResult, ClusterItem, SessionClusteringResponse, SemanticGroup
from ..models.llm_models import LLMRequest
from .llm_service import LLMService
from .embedding_service import EmbeddingService

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
    """LLM-driven clustering service: identifies clusters and assigns items per session."""

    def __init__(self, mapping_service=None, embedding_service: Optional[EmbeddingService] = None):
        self.llm_service = LLMService()  # TODO: should inject via constructor
        self.max_tokens = settings.clustering_max_tokens
        self.mapping_service = mapping_service
        self.embedding_service = embedding_service or EmbeddingService()

    async def cluster_session(self, session: HistorySession, user_id: int, force: bool = False) -> SessionClusteringResponse:
        """
        Cluster session using SemanticGroup compression and embedding-based similarity.
        
        Workflow:
        1. Check cache - return if already analyzed
        2. Create SemanticGroups (compression by title+hostname)
        3. Embed SemanticGroups (fewer API calls)
        4. LLM generates thematic clusters from groups
        5. Embed clusters
        6. Assign groups to clusters via cosine similarity
        7. Decompress groups back to items
        8. Build response, save to DB, return
        """
        # Canonicalize identifier with user scope to avoid cross-user collisions
        session.session_identifier = f"u{user_id}:{session.session_identifier}"
        logger.info(f"📊 Processing session {session.session_identifier} with {len(session.items)} items (force={force})")
        
        # Step 1: Check cache
        if self.mapping_service and not force:
            cached_result = self.mapping_service.get_clustering_result(session.session_identifier)
            if cached_result:
                logger.info(f"✅ Found cached result for session {session.session_identifier}, returning without processing")
                return cached_result
            logger.info(f"🆕 No cached result found, proceeding with clustering")

        # Step 2: Create SemanticGroups (compression)
        groups = self._create_semantic_groups(session)
        logger.info(f"📦 Compressed {len(session.items)} items into {len(groups)} semantic groups")

        # Step 3: Embed SemanticGroups
        groups = await self._embed_semantic_groups(groups)

        # Step 4: LLM generates thematic clusters from groups
        clusters_meta = await self.identify_clusters_from_groups(groups)
        logger.info(f"🎯 LLM identified {len(clusters_meta)} thematic clusters")

        # Step 5: Embed clusters based on theme + summary
        clusters_meta = await self._embed_clusters(clusters_meta)

        # Step 6: Assign groups to clusters via cosine similarity
        cluster_id_to_groups = self._assign_groups_by_similarity(groups, clusters_meta)

        # Step 7: Decompress groups back to items
        cluster_id_to_items = self._decompress_groups_to_items(cluster_id_to_groups)

        # Step 8: Build ClusterResult objects
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

        # Add hardcoded Generic cluster if it has items
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

        # Create session response
        response = SessionClusteringResponse(
            session_identifier=session.session_identifier,
            session_start_time=session.start_time,
            session_end_time=session.end_time,
            clusters=cluster_results
        )

        # Log ClusterResult models
        for cluster_result in cluster_results:
            log_payload = cluster_result.model_dump()
            log_payload.pop("embedding", None)
            for item_payload in log_payload.get("items", []):
                item_payload.pop("embedding", None)
            logger.info(f"🎯 ClusterResult: {log_payload}")
        
        # Step 9: Save to database
        if self.mapping_service:
            try:
                session_id = self.mapping_service.save_clustering_result(user_id, response, replace_if_exists=force)
                logger.info(f"💾 Saved clustering result to database with session_id: {session_id}")
            except Exception as e:
                logger.error(f"❌ Failed to save clustering result to database: {e}")
                # Don't fail the request, just log the error

        return response

    def _build_item_embedding_text(self, item: Any) -> Optional[str]:
        """Build embedding text from a HistoryItem or ClusterItem."""
        parts: List[str] = []
        if item.title:
            parts.append(item.title)
        if item.url_hostname:
            parts.append(item.url_hostname)
        if item.url_pathname_clean:
            parts.append(item.url_pathname_clean)
        if item.url_search_query:
            parts.append(item.url_search_query)

        if not parts:
            return None

        text = " | ".join(part.strip() for part in parts if part)
        return text[:1200]

    def _build_cluster_meta_embedding_text(self, cluster_meta: Dict[str, Any]) -> str:
        """Build embedding text from cluster metadata (theme + summary)."""
        theme = cluster_meta.get("theme", "")
        summary = cluster_meta.get("summary", "")
        text = f"{theme} - {summary}" if summary else theme
        return text.strip()[:1200]

    def _create_semantic_groups(self, session: HistorySession) -> List[SemanticGroup]:
        """
        Group session items by (title, hostname) to reduce redundant embeddings.
        Items with empty/null title become individual groups (group of 1).
        """
        groups_dict: Dict[str, List] = {}
        no_title_counter = 0
        
        for item in session.items:
            title = item.title.strip() if item.title else ""
            hostname = item.url_hostname or ""
            
            # Items with empty title become individual groups
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
        Embed each SemanticGroup once based on title + hostname + example_pathname_clean.
        Returns groups with embedding field populated.
        """
        if not self.embedding_service or not groups:
            return groups

        # Build embedding text for each group
        group_texts: List[str] = []
        group_indices: List[int] = []
        
        for idx, group in enumerate(groups):
            parts: List[str] = []
            if group.title:
                parts.append(group.title)
            if group.hostname:
                parts.append(group.hostname)
            if group.example_pathname_clean:
                parts.append(group.example_pathname_clean)
            
            if parts:
                text = " | ".join(part.strip() for part in parts if part)[:1200]
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
        """
        Embed clusters based on their theme and summary.
        Returns clusters_meta with 'embedding' field added.
        """
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
        """
        Assign SemanticGroups to clusters based on cosine similarity between embeddings.
        
        Args:
            groups: List of SemanticGroups with embeddings
            clusters_with_embeddings: List of cluster metadata with 'embedding' field
        
        Returns:
            Dict mapping cluster_id to list of SemanticGroups assigned to it
        """
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
            
            # If group has no embedding, assign to generic
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
            
            # Assign to best cluster if above threshold, otherwise to generic
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
                # Each item in the group gets the group's embedding
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
        """
        Use LLM to propose thematic clusters from SemanticGroups.
        
        This method receives compressed groups (title+hostname with visit counts)
        instead of individual items, reducing LLM input tokens significantly.
        
        Note: This method only returns thematic clusters identified by the LLM.
        The generic/fallback cluster is hardcoded and handled separately in cluster_session.
        """
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
            "Given the list of browsing activity groups (each group represents pages with the same title on a domain, "
            "with visit_count indicating how many times the user visited), identify between 1 and 10 THEMATIC clusters.\n"
            "Focus on identifying coherent themes - groups that don't fit will be handled separately.\n\n"
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
            f"Browsing activity groups:\n{json.dumps(simplified_groups, ensure_ascii=False)}\n"
        )

        try:
            req = LLMRequest(prompt=prompt, provider=settings.default_provider, max_tokens=self.max_tokens, temperature=settings.clustering_temperature)
            resp = await self.llm_service.generate_text(req)
            raw = resp.generated_text.strip()
            
            data = self._extract_json(raw)
            if isinstance(data, list):
                # Basic schema cleanup - only keep thematic clusters
                cleaned: List[Dict[str, Any]] = []
                
                for idx, c in enumerate(data):
                    if not isinstance(c, dict):
                        continue
                    cid = str(c.get("cluster_id") or f"cluster_{idx+1}")
                    theme = str(c.get("theme") or "Miscellaneous")
                    summary = str(c.get("summary") or "")
                    
                    # Skip if LLM generated a generic cluster (we handle that separately)
                    if cid == "cluster_generic":
                        continue
                    
                    cleaned.append({"cluster_id": cid, "theme": theme, "summary": summary})
                
                return cleaned
        except Exception as e:
            logger.error(f"LLM cluster identification from groups failed: {e}")

        # Fallback: empty list (all groups will go to hardcoded generic cluster)
        return []

    def _prepare_groups_for_llm(self, groups: List[SemanticGroup]) -> List[Dict[str, Any]]:
        """Return compressed group info for LLM: title, hostname, visit_count, example_visit_time, example_pathname_clean."""
        return [
            {
                "title": g.title,
                "hostname": g.hostname,
                "visit_count": g.item_count,
                "example_visit_time": g.example_visit_time.isoformat(),
                "example_pathname_clean": g.example_pathname_clean,
            }
            for g in groups
        ]

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


