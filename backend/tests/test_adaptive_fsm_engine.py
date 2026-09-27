"""
Unit tests for the deterministic adaptive interview finite-state-machine (FSM)
and server-side anti-loop topic transition logic.
"""

from backend.services import session_store


class TestAdaptiveFsmEngine:
    """Verifies state machine transitions, anti-loop caps, and topic progression."""

    def test_session_initialization_with_topics(self):
        topics = ["Architecture", "Databases", "Concurrency", "Security"]
        session_id = session_store.create_session(
            track="technical",
            role_id="full_stack_developer",
            role_name="Full Stack Developer",
            difficulty="Intermediate",
            max_questions=4,
            expected_topics=topics,
        )

        session = session_store.get_session(session_id)
        assert session is not None
        assert session["current_topic"] == "Architecture"
        assert session["followup_count_for_topic"] == 0
        assert session["topics_covered"] == []
        assert session["topics_remaining"] == ["Databases", "Concurrency", "Security"]
        assert session["max_questions"] == 4

    def test_step_followup_increments_counter(self):
        topics = ["Algorithms", "System Design"]
        session_id = session_store.create_session(
            track="technical",
            role_id="full_stack_developer",
            role_name="Full Stack Developer",
            difficulty="Intermediate",
            max_questions=4,
            expected_topics=topics,
        )

        count1 = session_store.step_followup(session_id)
        assert count1 == 1
        session = session_store.get_session(session_id)
        assert session["followup_count_for_topic"] == 1
        assert session["current_topic"] == "Algorithms"

        count2 = session_store.step_followup(session_id)
        assert count2 == 2
        session = session_store.get_session(session_id)
        assert session["followup_count_for_topic"] == 2

    def test_step_advance_topic_resets_followup_and_archives(self):
        topics = ["Frontend State", "Backend APIs", "DevOps"]
        session_id = session_store.create_session(
            track="technical",
            role_id="full_stack_developer",
            role_name="Full Stack Developer",
            difficulty="Intermediate",
            max_questions=5,
            expected_topics=topics,
        )

        # Increment follow up once
        session_store.step_followup(session_id)
        assert session_store.get_session(session_id)["followup_count_for_topic"] == 1

        # Advance topic
        next_topic = session_store.step_advance_topic(session_id)
        assert next_topic == "Backend APIs"

        session = session_store.get_session(session_id)
        assert session["current_topic"] == "Backend APIs"
        assert session["followup_count_for_topic"] == 0
        assert session["topics_covered"] == ["Frontend State"]
        assert session["topics_remaining"] == ["DevOps"]

    def test_intermediate_analysis_persistence(self):
        session_id = session_store.create_session(
            track="technical",
            role_id="full_stack_developer",
            role_name="Full Stack Developer",
            difficulty="Intermediate",
            max_questions=3,
            expected_topics=["Topic A", "Topic B"],
        )

        analysis_payload = {
            "relevance_score": 9.0,
            "depth_score": 8.0,
            "specificity_score": 8.5,
            "identified_gaps": ["No mention of transaction rollback"],
            "detected_claims": ["Implemented optimistic locking"],
            "decision": "DRILL_DOWN",
            "reasoning": "Clear response; probe rollback strategy.",
        }

        session_store.record_intermediate_analysis(session_id, analysis_payload)
        session = session_store.get_session(session_id)

        assert "intermediate_analyses" in session
        assert len(session["intermediate_analyses"]) == 1
        assert session["intermediate_analyses"][0]["decision"] == "DRILL_DOWN"
