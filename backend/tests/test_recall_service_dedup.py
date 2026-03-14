from datetime import datetime
from typing import Dict, List
from unittest.mock import MagicMock

import pytest

from app.modules.recall_engine.application.recall_service import RecallService


OBSERVED_AT = datetime(2026, 3, 1, 10, 0, 0)
USER_ID = 42
SESSION_IDENTIFIER = "session-dedup-test"


def _build_clusters() -> List[Dict]:
    """Mock output already produced by the LLM clustering step."""
    return [
        {
            "id": "c_asyncio_1",
            "theme": "Python asyncio deep dive",
            "summary": "Learned event loops and coroutines",
            "is_learning": True,
            "embedding": [0.11, 0.22, 0.33],
            "items": [{"url": "https://docs.python.org/3/library/asyncio.html"}],
        },
        {
            "id": "c_asyncio_2",
            "theme": "Asyncio event loop internals",
            "summary": "Same topic, phrased differently",
            "is_learning": True,
            "embedding": [0.12, 0.23, 0.34],
            "items": [{"url": "https://realpython.com/async-io-python/"}],
        },
        {
            "id": "c_etf_1",
            "theme": "ETF long-term investing",
            "summary": "A distinct topic that should stay separate",
            "is_learning": True,
            "embedding": [0.91, 0.82, 0.73],
            "items": [{"url": "https://www.investopedia.com/"}],
        },
    ]


def _compute_dedup_metrics(predicted_topic_ids: List[int], expected_topic_groups: List[str]) -> Dict[str, float]:
    """
    Evaluate dedup quality from cluster-to-topic assignments.
    - dedup_precision: among predicted merges, how many are correct
    - over_merge_rate: among non-duplicate ground truth clusters, how many were incorrectly merged
    """
    seen_predicted_topic_ids = set()
    seen_expected_groups = set()
    true_positive = 0
    false_positive = 0
    expected_non_duplicates = 0

    for predicted_topic_id, expected_group in zip(predicted_topic_ids, expected_topic_groups):
        predicted_merge = predicted_topic_id in seen_predicted_topic_ids
        expected_merge = expected_group in seen_expected_groups

        if predicted_merge and expected_merge:
            true_positive += 1
        elif predicted_merge and not expected_merge:
            false_positive += 1

        if not expected_merge:
            expected_non_duplicates += 1

        seen_predicted_topic_ids.add(predicted_topic_id)
        seen_expected_groups.add(expected_group)

    predicted_merges = true_positive + false_positive
    dedup_precision = true_positive / predicted_merges if predicted_merges else 1.0
    over_merge_rate = false_positive / expected_non_duplicates if expected_non_duplicates else 0.0

    return {
        "dedup_precision": dedup_precision,
        "over_merge_rate": over_merge_rate,
        "true_positive": float(true_positive),
        "false_positive": float(false_positive),
    }


@pytest.fixture
def service_with_mocks():
    topic_repository = MagicMock()
    session_repository = MagicMock()
    service = RecallService(topic_repository=topic_repository, session_repository=session_repository)

    session_repository.get_session_by_identifier.return_value = {
        "id": 1001,
        "end_time": OBSERVED_AT,
    }
    topic_repository.list_topics_with_state.return_value = []
    topic_repository.upsert_recall_state.return_value = {"topic_id": 0}
    topic_repository.create_recall_event.return_value = {"id": 1}
    topic_repository.add_observation.return_value = {"id": 1}
    return service, topic_repository


@pytest.mark.parametrize(
    "matched_by_cluster_id, expected_precision, expected_over_merge",
    [
        # Good behavior: only truly similar cluster is merged.
        (
            {
                "c_asyncio_2": {"id": 2001, "name": "Python asyncio deep dive", "description": "existing"},
            },
            1.0,
            0.0,
        ),
        # Over-merge behavior: ETF cluster wrongly merged into asyncio topic.
        (
            {
                "c_asyncio_2": {"id": 2001, "name": "Python asyncio deep dive", "description": "existing"},
                "c_etf_1": {"id": 2001, "name": "Python asyncio deep dive", "description": "existing"},
            },
            0.5,
            1 / 2,
        ),
    ],
)
def test_ingest_clustered_session_dedup_metrics(
    service_with_mocks,
    matched_by_cluster_id,
    expected_precision,
    expected_over_merge,
):
    service, topic_repository = service_with_mocks
    clusters = _build_clusters()

    # Arrange
    def find_similar_side_effect(_user_id, embedding):
        by_embedding = {
            (0.11, 0.22, 0.33): "c_asyncio_1",
            (0.12, 0.23, 0.34): "c_asyncio_2",
            (0.91, 0.82, 0.73): "c_etf_1",
        }
        cluster_id = by_embedding[tuple(embedding)]
        return matched_by_cluster_id.get(cluster_id)

    def get_or_create_side_effect(user_id, name, description=None, embedding=None):
        if name == "Python asyncio deep dive":
            return {"id": 2001, "name": name, "description": description, "embedding": embedding}
        if name == "ETF long-term investing":
            return {"id": 3001, "name": name, "description": description, "embedding": embedding}
        raise AssertionError(f"Unexpected topic name in test fixture: {name}")

    topic_repository.find_similar_topic.side_effect = find_similar_side_effect
    topic_repository.get_or_create_topic.side_effect = get_or_create_side_effect

    # Act
    service.ingest_clustered_session(
        user_id=USER_ID,
        session_identifier=SESSION_IDENTIFIER,
        clusters=clusters,
    )

    predicted_topic_ids = [call.args[0] for call in topic_repository.add_observation.call_args_list]
    expected_topic_groups = ["python_asyncio", "python_asyncio", "etf_investing"]
    metrics = _compute_dedup_metrics(predicted_topic_ids, expected_topic_groups)

    # Assert
    assert metrics["dedup_precision"] == pytest.approx(expected_precision)
    assert metrics["over_merge_rate"] == pytest.approx(expected_over_merge)
    assert topic_repository.add_observation.call_count == 3
    assert topic_repository.upsert_recall_state.call_count == 3
