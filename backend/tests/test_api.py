"""Tests for the FastAPI API endpoints.

Uses a test app (defined in conftest.py) that mirrors the real endpoints
but avoids the static file mount that requires the frontend directory.
"""


class TestQueryEndpoint:
    """Tests for POST /api/query"""

    def test_query_returns_answer_and_sources(self, client, mock_rag_system):
        response = client.post("/api/query", json={"query": "What is Python?"})

        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "Python is a programming language."
        assert len(data["sources"]) == 1
        assert data["sources"][0]["name"] == "Intro to Python - Lesson 1"
        mock_rag_system.query.assert_called_once_with("What is Python?", "test-session-123")

    def test_query_creates_session_when_not_provided(self, client, mock_rag_system):
        response = client.post("/api/query", json={"query": "Hello"})

        assert response.status_code == 200
        mock_rag_system.session_manager.create_session.assert_called_once()
        assert response.json()["session_id"] == "test-session-123"

    def test_query_uses_provided_session_id(self, client, mock_rag_system):
        response = client.post(
            "/api/query", json={"query": "Hello", "session_id": "existing-session"}
        )

        assert response.status_code == 200
        assert response.json()["session_id"] == "existing-session"
        mock_rag_system.session_manager.create_session.assert_not_called()
        mock_rag_system.query.assert_called_once_with("Hello", "existing-session")

    def test_query_returns_500_on_rag_error(self, client, mock_rag_system):
        mock_rag_system.query.side_effect = RuntimeError("Vector store unavailable")

        response = client.post("/api/query", json={"query": "test"})

        assert response.status_code == 500
        assert "Vector store unavailable" in response.json()["detail"]

    def test_query_requires_query_field(self, client):
        response = client.post("/api/query", json={})

        assert response.status_code == 422

    def test_query_rejects_non_json_body(self, client):
        response = client.post("/api/query", content="not json")

        assert response.status_code == 422

    def test_query_with_empty_sources(self, client, mock_rag_system):
        mock_rag_system.query.return_value = ("No results found.", [])

        response = client.post("/api/query", json={"query": "unknown topic"})

        assert response.status_code == 200
        data = response.json()
        assert data["sources"] == []
        assert data["answer"] == "No results found."


class TestCoursesEndpoint:
    """Tests for GET /api/courses"""

    def test_courses_returns_stats(self, client):
        response = client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == 2
        assert data["course_titles"] == ["Intro to Python", "Advanced ML"]

    def test_courses_returns_500_on_error(self, client, mock_rag_system):
        mock_rag_system.get_course_analytics.side_effect = RuntimeError("DB error")

        response = client.get("/api/courses")

        assert response.status_code == 500
        assert "DB error" in response.json()["detail"]

    def test_courses_with_no_courses(self, client, mock_rag_system):
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 0,
            "course_titles": [],
        }

        response = client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == 0
        assert data["course_titles"] == []
