"""
In-memory metrics collector for tracking application performance and usage.

This singleton class aggregates metrics across all requests and provides
a summary endpoint for monitoring. Metrics are reset on server restart.
"""

import threading
from collections import defaultdict
from typing import Dict, Any, List
from statistics import mean


class MetricsCollector:
    """Thread-safe singleton for collecting application metrics."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize all metric counters."""
        self._data_lock = threading.Lock()
        
        # LLM metrics
        self.llm_calls = 0
        self.llm_tokens_in = 0
        self.llm_tokens_out = 0
        self.llm_total_cost = 0.0
        self.llm_total_duration_ms = 0.0
        self.llm_by_provider: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "calls": 0, 
                "tokens_in": 0, 
                "tokens_out": 0,
                "cost": 0.0,
                "durations_ms": []
            }
        )
        
        # Chat metrics
        self.chat_total_requests = 0
        self.chat_total_turns = 0
        self.chat_tool_calls_by_name: Dict[str, int] = defaultdict(int)
        self.chat_durations_ms: List[float] = []
        
        # Clustering metrics
        self.clustering_total_sessions = 0
        self.clustering_cache_hits = 0
        self.clustering_cache_misses = 0
        self.clustering_groups_created: List[int] = []
        self.clustering_clusters_created: List[int] = []
        self.clustering_durations_ms: List[float] = []
        
        # Search metrics
        self.search_total_queries = 0
        self.search_empty_results = 0
        self.search_clusters_returned: List[int] = []
        self.search_items_returned: List[int] = []
        
        # Embedding metrics
        self.embedding_total_batches = 0
        self.embedding_total_texts = 0
        self.embedding_failures = 0
        self.embedding_durations_ms: List[float] = []
    
    def record_llm_call(
        self, 
        provider: str, 
        model: str,
        tokens_in: int, 
        tokens_out: int, 
        duration_ms: float,
        cost: float
    ):
        """Record an LLM API call."""
        with self._data_lock:
            self.llm_calls += 1
            self.llm_tokens_in += tokens_in
            self.llm_tokens_out += tokens_out
            self.llm_total_cost += cost
            self.llm_total_duration_ms += duration_ms
            
            provider_data = self.llm_by_provider[provider]
            provider_data["calls"] += 1
            provider_data["tokens_in"] += tokens_in
            provider_data["tokens_out"] += tokens_out
            provider_data["cost"] += cost
            provider_data["durations_ms"].append(duration_ms)
    
    def record_chat_completion(self, turns: int, tool_calls: List[str], duration_ms: float):
        """Record a completed chat request."""
        with self._data_lock:
            self.chat_total_requests += 1
            self.chat_total_turns += turns
            self.chat_durations_ms.append(duration_ms)
            
            for tool_name in tool_calls:
                self.chat_tool_calls_by_name[tool_name] += 1
    
    def record_clustering(self, cached: bool, groups: int, clusters: int, duration_ms: float):
        """Record a clustering operation."""
        with self._data_lock:
            self.clustering_total_sessions += 1
            
            if cached:
                self.clustering_cache_hits += 1
            else:
                self.clustering_cache_misses += 1
                self.clustering_groups_created.append(groups)
                self.clustering_clusters_created.append(clusters)
                self.clustering_durations_ms.append(duration_ms)
    
    def record_search(self, clusters_found: int, items_found: int):
        """Record a search operation."""
        with self._data_lock:
            self.search_total_queries += 1
            
            if clusters_found == 0:
                self.search_empty_results += 1
            
            self.search_clusters_returned.append(clusters_found)
            self.search_items_returned.append(items_found)
    
    def record_embedding(self, batch_size: int, failures: int, duration_ms: float):
        """Record an embedding batch operation."""
        with self._data_lock:
            self.embedding_total_batches += 1
            self.embedding_total_texts += batch_size
            self.embedding_failures += failures
            self.embedding_durations_ms.append(duration_ms)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all collected metrics.
        
        Returns:
            Dictionary containing aggregated metrics
        """
        with self._data_lock:
            # Process provider data for output
            provider_summary = {}
            for provider, data in self.llm_by_provider.items():
                avg_duration = mean(data["durations_ms"]) if data["durations_ms"] else 0
                provider_summary[provider] = {
                    "calls": data["calls"],
                    "tokens_in": data["tokens_in"],
                    "tokens_out": data["tokens_out"],
                    "cost_usd": round(data["cost"], 4),
                    "avg_latency_ms": round(avg_duration, 2)
                }
            
            return {
                "llm": {
                    "total_calls": self.llm_calls,
                    "total_tokens_in": self.llm_tokens_in,
                    "total_tokens_out": self.llm_tokens_out,
                    "total_tokens": self.llm_tokens_in + self.llm_tokens_out,
                    "total_cost_usd": round(self.llm_total_cost, 4),
                    "avg_latency_ms": round(
                        self.llm_total_duration_ms / self.llm_calls, 2
                    ) if self.llm_calls else 0,
                    "by_provider": provider_summary
                },
                "chat": {
                    "total_requests": self.chat_total_requests,
                    "total_turns": self.chat_total_turns,
                    "avg_turns_per_request": round(
                        self.chat_total_turns / self.chat_total_requests, 2
                    ) if self.chat_total_requests else 0,
                    "avg_duration_ms": round(
                        mean(self.chat_durations_ms), 2
                    ) if self.chat_durations_ms else 0,
                    "tool_calls": dict(self.chat_tool_calls_by_name)
                },
                "clustering": {
                    "total_sessions": self.clustering_total_sessions,
                    "cache_hits": self.clustering_cache_hits,
                    "cache_misses": self.clustering_cache_misses,
                    "cache_hit_rate": round(
                        self.clustering_cache_hits / self.clustering_total_sessions, 3
                    ) if self.clustering_total_sessions else 0,
                    "avg_groups_created": round(
                        mean(self.clustering_groups_created), 2
                    ) if self.clustering_groups_created else 0,
                    "avg_clusters_created": round(
                        mean(self.clustering_clusters_created), 2
                    ) if self.clustering_clusters_created else 0,
                    "avg_duration_ms": round(
                        mean(self.clustering_durations_ms), 2
                    ) if self.clustering_durations_ms else 0
                },
                "search": {
                    "total_queries": self.search_total_queries,
                    "empty_results": self.search_empty_results,
                    "empty_result_rate": round(
                        self.search_empty_results / self.search_total_queries, 3
                    ) if self.search_total_queries else 0,
                    "avg_clusters_returned": round(
                        mean(self.search_clusters_returned), 2
                    ) if self.search_clusters_returned else 0,
                    "avg_items_returned": round(
                        mean(self.search_items_returned), 2
                    ) if self.search_items_returned else 0
                },
                "embeddings": {
                    "total_batches": self.embedding_total_batches,
                    "total_texts": self.embedding_total_texts,
                    "total_failures": self.embedding_failures,
                    "failure_rate": round(
                        self.embedding_failures / self.embedding_total_texts, 3
                    ) if self.embedding_total_texts else 0,
                    "avg_duration_ms": round(
                        mean(self.embedding_durations_ms), 2
                    ) if self.embedding_durations_ms else 0
                }
            }


# Singleton instance
metrics = MetricsCollector()
