"""Tests for the agentforge A2A (Agent-to-Agent) protocol modules.

Tests for:
- A2A type creation and validation (a2a_types.py)
- A2ABridge: agent-to-card conversion, server/client creation, remote calls
- A2AClient: initialization, discovery, send_task, get_task, cancel, list, polling
- A2AServer: message handling, capability registration, task lifecycle, cleanup
- Error handling: invalid messages, connection failures, timeouts
"""

import asyncio
import json
import urllib.error
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from agentforge.comms.a2a_bridge import A2ABridge
from agentforge.comms.a2a_client import A2AClient, A2AClientError
from agentforge.comms.a2a_server import A2AServer
from agentforge.comms.a2a_types import (
    A2AErrorCode,
    A2AMessage,
    A2AResponse,
    AgentCapability,
    AgentCard,
    Task,
    TaskStatus,
    TaskUpdate,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_capability() -> AgentCapability:
    """Create a sample AgentCapability."""
    return AgentCapability(
        name="get_forecast",
        description="Get weather forecast for a location",
        input_schema={
            "type": "object",
            "properties": {"location": {"type": "string"}},
        },
        output_schema={
            "type": "object",
            "properties": {"forecast": {"type": "string"}},
        },
    )


@pytest.fixture
def sample_card(sample_capability: AgentCapability) -> AgentCard:
    """Create a sample AgentCard."""
    return AgentCard(
        id="weather-agent",
        name="WeatherAgent",
        description="Provides weather forecasts",
        version="2.0.0",
        capabilities=[sample_capability],
        endpoints={"tasks": "/a2a", "card": "/.well-known/agent.json"},
        metadata={"owner": "test"},
    )


@pytest.fixture
def server(sample_card: AgentCard) -> A2AServer:
    """Create a sample A2AServer."""
    return A2AServer(sample_card)


@pytest.fixture
def client() -> A2AClient:
    """Create a sample A2AClient."""
    return A2AClient("https://agent.example.com")


# ---------------------------------------------------------------------------
# A2A Types Tests
# ---------------------------------------------------------------------------


class TestAgentCapability:
    """Tests for AgentCapability."""

    def test_create_capability(self) -> None:
        cap = AgentCapability(
            name="search",
            description="Search for documents",
            input_schema={"type": "object"},
            output_schema={"type": "array"},
        )
        assert cap.name == "search"
        assert cap.description == "Search for documents"
        assert cap.input_schema == {"type": "object"}
        assert cap.output_schema == {"type": "array"}

    def test_capability_defaults(self) -> None:
        cap = AgentCapability(name="test", description="Test capability")
        assert cap.input_schema == {}
        assert cap.output_schema == {}

    def test_capability_serialization(self) -> None:
        cap = AgentCapability(name="test", description="Test")
        data = cap.model_dump()
        assert data["name"] == "test"
        restored = AgentCapability(**data)
        assert restored.name == cap.name


class TestAgentCard:
    """Tests for AgentCard (a2a_types version)."""

    def test_create_card(self, sample_card: AgentCard) -> None:
        assert sample_card.id == "weather-agent"
        assert sample_card.name == "WeatherAgent"
        assert sample_card.version == "2.0.0"
        assert len(sample_card.capabilities) == 1
        assert sample_card.endpoints["tasks"] == "/a2a"
        assert sample_card.metadata["owner"] == "test"

    def test_card_defaults(self) -> None:
        card = AgentCard(id="x", name="X")
        assert card.description == ""
        assert card.version == "1.0.0"
        assert card.capabilities == []
        assert card.endpoints == {}
        assert card.metadata == {}
        assert card.created_at is not None

    def test_card_to_json(self, sample_card: AgentCard) -> None:
        data = sample_card.to_json()
        assert isinstance(data, dict)
        assert data["id"] == "weather-agent"
        assert data["name"] == "WeatherAgent"
        assert len(data["capabilities"]) == 1

    def test_card_round_trip(self, sample_card: AgentCard) -> None:
        data = sample_card.to_json()
        restored = AgentCard(**data)
        assert restored.id == sample_card.id
        assert restored.name == sample_card.name
        assert len(restored.capabilities) == len(sample_card.capabilities)


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_all_statuses_exist(self) -> None:
        assert TaskStatus.SUBMITTED == "submitted"
        assert TaskStatus.WORKING == "working"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"
        assert TaskStatus.CANCELLED == "cancelled"

    def test_status_is_string(self) -> None:
        assert isinstance(TaskStatus.SUBMITTED, str)
        assert TaskStatus.COMPLETED.value == "completed"


class TestTask:
    """Tests for Task."""

    def test_create_task(self) -> None:
        task = Task(
            agent_id="agent-1",
            input={"message": "Hello"},
            metadata={"capability": "chat"},
        )
        assert task.agent_id == "agent-1"
        assert task.status == TaskStatus.SUBMITTED
        assert task.input == {"message": "Hello"}
        assert task.output is None
        assert task.error is None
        assert task.id is not None
        assert task.created_at is not None

    def test_task_defaults(self) -> None:
        task = Task()
        assert task.agent_id == ""
        assert task.status == TaskStatus.SUBMITTED
        assert task.input == {}
        assert task.metadata == {}

    def test_task_touch_updates_timestamp(self) -> None:
        task = Task()
        original_updated = task.updated_at
        # Small sleep to ensure timestamp changes
        import time

        time.sleep(0.01)
        task.touch()
        assert task.updated_at != original_updated

    def test_task_unique_ids(self) -> None:
        t1 = Task()
        t2 = Task()
        assert t1.id != t2.id

    def test_task_serialization(self) -> None:
        task = Task(
            agent_id="test-agent",
            status=TaskStatus.COMPLETED,
            input={"q": "hello"},
            output={"a": "world"},
        )
        data = task.model_dump()
        assert data["agent_id"] == "test-agent"
        assert data["status"] == "completed"
        restored = Task(**data)
        assert restored.output == {"a": "world"}


class TestTaskUpdate:
    """Tests for TaskUpdate."""

    def test_create_task_update(self) -> None:
        update = TaskUpdate(
            task_id="task-1",
            status=TaskStatus.COMPLETED,
            output={"result": "done"},
        )
        assert update.task_id == "task-1"
        assert update.status == TaskStatus.COMPLETED
        assert update.output == {"result": "done"}
        assert update.error is None
        assert update.metadata is None

    def test_task_update_error(self) -> None:
        update = TaskUpdate(
            task_id="task-2",
            status=TaskStatus.FAILED,
            error="Something went wrong",
        )
        assert update.error == "Something went wrong"

    def test_task_update_partial(self) -> None:
        update = TaskUpdate(task_id="task-3", metadata={"extra": "info"})
        assert update.status is None
        assert update.output is None
        assert update.metadata == {"extra": "info"}


class TestA2AMessage:
    """Tests for A2AMessage."""

    def test_create_message(self) -> None:
        msg = A2AMessage(
            method="tasks/send",
            params={"capability": "search", "input": {"q": "test"}},
            id="req-001",
        )
        assert msg.jsonrpc == "2.0"
        assert msg.method == "tasks/send"
        assert msg.params["capability"] == "search"
        assert msg.id == "req-001"

    def test_message_defaults(self) -> None:
        msg = A2AMessage(method="agent/card")
        assert msg.jsonrpc == "2.0"
        assert msg.params == {}
        assert msg.id is None

    def test_message_serialization(self) -> None:
        msg = A2AMessage(method="tasks/get", params={"task_id": "t-1"}, id="r-1")
        data = msg.model_dump()
        assert data["jsonrpc"] == "2.0"
        assert data["method"] == "tasks/get"
        restored = A2AMessage(**data)
        assert restored.id == "r-1"


class TestA2AResponse:
    """Tests for A2AResponse."""

    def test_success_response(self) -> None:
        resp = A2AResponse(id="req-001", result={"forecast": "Sunny"})
        assert resp.jsonrpc == "2.0"
        assert resp.result == {"forecast": "Sunny"}
        assert resp.error is None

    def test_error_response(self) -> None:
        resp = A2AResponse(
            id="req-001",
            error={"code": -32602, "message": "Invalid params"},
        )
        assert resp.error["code"] == -32602
        assert resp.result is None

    def test_response_defaults(self) -> None:
        resp = A2AResponse()
        assert resp.jsonrpc == "2.0"
        assert resp.result is None
        assert resp.error is None
        assert resp.id is None


class TestA2AErrorCode:
    """Tests for A2AErrorCode constants."""

    def test_standard_error_codes(self) -> None:
        assert A2AErrorCode.PARSE_ERROR == -32700
        assert A2AErrorCode.INVALID_REQUEST == -32600
        assert A2AErrorCode.METHOD_NOT_FOUND == -32601
        assert A2AErrorCode.INVALID_PARAMS == -32602
        assert A2AErrorCode.INTERNAL_ERROR == -32603

    def test_a2a_specific_error_codes(self) -> None:
        assert A2AErrorCode.TASK_NOT_FOUND == -32001
        assert A2AErrorCode.CAPABILITY_NOT_FOUND == -32002
        assert A2AErrorCode.TASK_EXECUTION_FAILED == -32003
        assert A2AErrorCode.AGENT_UNAVAILABLE == -32004


# ---------------------------------------------------------------------------
# A2AServer Tests
# ---------------------------------------------------------------------------


class TestA2AServer:
    """Tests for A2AServer."""

    def test_server_init(self, server: A2AServer, sample_card: AgentCard) -> None:
        assert server.agent_card == sample_card
        assert server._tasks == {}

    def test_register_capability_handler(self, server: A2AServer) -> None:
        async def handler(data: dict[str, Any]) -> dict[str, Any]:
            return {"result": "ok"}

        server.register_capability_handler("get_forecast", handler)
        assert "get_forecast" in server._task_handlers

    def test_unregister_capability_handler(self, server: A2AServer) -> None:
        async def handler(data: dict[str, Any]) -> dict[str, Any]:
            return {}

        server.register_capability_handler("test_cap", handler)
        assert server.unregister_capability_handler("test_cap") is True
        assert "test_cap" not in server._task_handlers

    def test_unregister_missing_handler(self, server: A2AServer) -> None:
        assert server.unregister_capability_handler("nonexistent") is False

    @pytest.mark.asyncio
    async def test_handle_task_send_success(self, server: A2AServer) -> None:
        async def handler(data: dict[str, Any]) -> dict[str, Any]:
            return {"forecast": "Sunny, 72F"}

        server.register_capability_handler("get_forecast", handler)

        msg = A2AMessage(
            method="tasks/send",
            params={"capability": "get_forecast", "input": {"location": "NYC"}},
            id="req-1",
        )
        resp = await server.handle_message(msg)

        assert resp.error is None
        assert resp.result is not None
        assert resp.result["status"] == "completed"
        assert resp.result["output"] == {"forecast": "Sunny, 72F"}

    @pytest.mark.asyncio
    async def test_handle_task_send_sync_handler(self, server: A2AServer) -> None:
        """Test that synchronous handlers are supported via asyncio.to_thread."""

        def sync_handler(data: dict[str, Any]) -> dict[str, Any]:
            return {"computed": True}

        server.register_capability_handler("get_forecast", sync_handler)

        msg = A2AMessage(
            method="tasks/send",
            params={"capability": "get_forecast", "input": {}},
            id="req-sync",
        )
        resp = await server.handle_message(msg)

        assert resp.error is None
        assert resp.result["status"] == "completed"
        assert resp.result["output"] == {"computed": True}

    @pytest.mark.asyncio
    async def test_handle_task_send_handler_returns_non_dict(self, server: A2AServer) -> None:
        """Test handler returning non-dict wraps in {'result': value}."""

        async def handler(data: dict[str, Any]) -> str:
            return "plain string result"

        server.register_capability_handler("get_forecast", handler)

        msg = A2AMessage(
            method="tasks/send",
            params={"capability": "get_forecast", "input": {}},
            id="req-nd",
        )
        resp = await server.handle_message(msg)

        assert resp.result["output"] == {"result": "plain string result"}

    @pytest.mark.asyncio
    async def test_handle_task_send_missing_capability(self, server: A2AServer) -> None:
        msg = A2AMessage(
            method="tasks/send",
            params={"input": {"location": "NYC"}},
            id="req-2",
        )
        resp = await server.handle_message(msg)

        assert resp.error is not None
        assert resp.error["code"] == A2AErrorCode.INVALID_PARAMS

    @pytest.mark.asyncio
    async def test_handle_task_send_unknown_capability(self, server: A2AServer) -> None:
        msg = A2AMessage(
            method="tasks/send",
            params={"capability": "nonexistent", "input": {}},
            id="req-3",
        )
        resp = await server.handle_message(msg)

        assert resp.error is not None
        assert resp.error["code"] == A2AErrorCode.INVALID_PARAMS

    @pytest.mark.asyncio
    async def test_handle_task_send_handler_error(self, server: A2AServer) -> None:
        async def failing_handler(data: dict[str, Any]) -> dict[str, Any]:
            raise RuntimeError("Handler crashed")

        server.register_capability_handler("get_forecast", failing_handler)

        msg = A2AMessage(
            method="tasks/send",
            params={"capability": "get_forecast", "input": {}},
            id="req-fail",
        )
        resp = await server.handle_message(msg)

        # Task should be marked failed, but the overall response is still a result
        assert resp.error is None
        assert resp.result["status"] == "failed"
        assert "Handler crashed" in resp.result["error"]

    @pytest.mark.asyncio
    async def test_handle_task_get_success(self, server: A2AServer) -> None:
        # Create a task first
        task = Task(agent_id="weather-agent", input={"location": "NYC"})
        server._tasks[task.id] = task

        msg = A2AMessage(
            method="tasks/get",
            params={"task_id": task.id},
            id="req-get",
        )
        resp = await server.handle_message(msg)

        assert resp.error is None
        assert resp.result["id"] == task.id

    @pytest.mark.asyncio
    async def test_handle_task_get_missing_id(self, server: A2AServer) -> None:
        msg = A2AMessage(method="tasks/get", params={}, id="req-noid")
        resp = await server.handle_message(msg)

        assert resp.error is not None
        assert resp.error["code"] == A2AErrorCode.INVALID_PARAMS

    @pytest.mark.asyncio
    async def test_handle_task_get_not_found(self, server: A2AServer) -> None:
        msg = A2AMessage(
            method="tasks/get",
            params={"task_id": "nonexistent"},
            id="req-404",
        )
        resp = await server.handle_message(msg)

        assert resp.error is not None

    @pytest.mark.asyncio
    async def test_handle_task_cancel_working(self, server: A2AServer) -> None:
        task = Task(agent_id="weather-agent", status=TaskStatus.WORKING)
        server._tasks[task.id] = task

        msg = A2AMessage(
            method="tasks/cancel",
            params={"task_id": task.id},
            id="req-cancel",
        )
        resp = await server.handle_message(msg)

        assert resp.error is None
        assert resp.result["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_handle_task_cancel_completed_no_change(self, server: A2AServer) -> None:
        task = Task(agent_id="weather-agent", status=TaskStatus.COMPLETED)
        server._tasks[task.id] = task

        msg = A2AMessage(
            method="tasks/cancel",
            params={"task_id": task.id},
            id="req-cancel-done",
        )
        resp = await server.handle_message(msg)

        assert resp.error is None
        assert resp.result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_handle_task_cancel_missing_id(self, server: A2AServer) -> None:
        msg = A2AMessage(method="tasks/cancel", params={}, id="req-cancel-noid")
        resp = await server.handle_message(msg)
        assert resp.error is not None

    @pytest.mark.asyncio
    async def test_handle_task_cancel_not_found(self, server: A2AServer) -> None:
        msg = A2AMessage(
            method="tasks/cancel",
            params={"task_id": "missing"},
            id="req-cancel-404",
        )
        resp = await server.handle_message(msg)
        assert resp.error is not None

    @pytest.mark.asyncio
    async def test_handle_task_list_empty(self, server: A2AServer) -> None:
        msg = A2AMessage(method="tasks/list", params={}, id="req-list")
        resp = await server.handle_message(msg)

        assert resp.error is None
        assert resp.result["tasks"] == []
        assert resp.result["total"] == 0

    @pytest.mark.asyncio
    async def test_handle_task_list_with_tasks(self, server: A2AServer) -> None:
        for _i in range(3):
            task = Task(agent_id="test", status=TaskStatus.COMPLETED)
            server._tasks[task.id] = task

        msg = A2AMessage(method="tasks/list", params={}, id="req-list-full")
        resp = await server.handle_message(msg)

        assert resp.error is None
        assert len(resp.result["tasks"]) == 3
        assert resp.result["total"] == 3

    @pytest.mark.asyncio
    async def test_handle_task_list_with_status_filter(self, server: A2AServer) -> None:
        t1 = Task(agent_id="test", status=TaskStatus.COMPLETED)
        t2 = Task(agent_id="test", status=TaskStatus.WORKING)
        t3 = Task(agent_id="test", status=TaskStatus.COMPLETED)
        server._tasks[t1.id] = t1
        server._tasks[t2.id] = t2
        server._tasks[t3.id] = t3

        msg = A2AMessage(
            method="tasks/list",
            params={"status": "completed"},
            id="req-list-filter",
        )
        resp = await server.handle_message(msg)

        assert len(resp.result["tasks"]) == 2

    @pytest.mark.asyncio
    async def test_handle_task_list_with_limit(self, server: A2AServer) -> None:
        for _ in range(5):
            task = Task(agent_id="test")
            server._tasks[task.id] = task

        msg = A2AMessage(
            method="tasks/list",
            params={"limit": 2},
            id="req-list-limit",
        )
        resp = await server.handle_message(msg)

        assert len(resp.result["tasks"]) == 2
        assert resp.result["total"] == 5

    @pytest.mark.asyncio
    async def test_handle_agent_card(self, server: A2AServer) -> None:
        msg = A2AMessage(method="agent/card", params={}, id="req-card")
        resp = await server.handle_message(msg)

        assert resp.error is None
        assert resp.result["id"] == "weather-agent"
        assert resp.result["name"] == "WeatherAgent"

    @pytest.mark.asyncio
    async def test_handle_unknown_method(self, server: A2AServer) -> None:
        msg = A2AMessage(method="unknown/method", params={}, id="req-unknown")
        resp = await server.handle_message(msg)

        assert resp.error is not None
        assert resp.error["code"] == A2AErrorCode.METHOD_NOT_FOUND

    @pytest.mark.asyncio
    async def test_handle_internal_error(self, server: A2AServer) -> None:
        """Test that unexpected exceptions in handlers return INTERNAL_ERROR."""

        async def bad_handler(params: dict[str, Any]) -> dict[str, Any]:
            raise TypeError("unexpected type")

        server._handlers["custom/fail"] = bad_handler

        msg = A2AMessage(method="custom/fail", params={}, id="req-internal")
        resp = await server.handle_message(msg)

        assert resp.error is not None
        assert resp.error["code"] == A2AErrorCode.INTERNAL_ERROR

    def test_get_well_known_response(self, server: A2AServer) -> None:
        response = server.get_well_known_response()
        data = json.loads(response)
        assert data["id"] == "weather-agent"
        assert data["name"] == "WeatherAgent"

    def test_get_task_by_id(self, server: A2AServer) -> None:
        task = Task(agent_id="test")
        server._tasks[task.id] = task

        found = server.get_task(task.id)
        assert found is not None
        assert found.id == task.id

    def test_get_task_by_id_not_found(self, server: A2AServer) -> None:
        assert server.get_task("nonexistent") is None

    def test_list_tasks_direct(self, server: A2AServer) -> None:
        t1 = Task(agent_id="test", status=TaskStatus.COMPLETED)
        t2 = Task(agent_id="test", status=TaskStatus.WORKING)
        server._tasks[t1.id] = t1
        server._tasks[t2.id] = t2

        all_tasks = server.list_tasks()
        assert len(all_tasks) == 2

        completed = server.list_tasks(status=TaskStatus.COMPLETED)
        assert len(completed) == 1

    def test_list_tasks_with_limit(self, server: A2AServer) -> None:
        for _ in range(5):
            task = Task(agent_id="test")
            server._tasks[task.id] = task

        limited = server.list_tasks(limit=3)
        assert len(limited) == 3

    def test_clear_completed_tasks(self, server: A2AServer) -> None:
        old_time = (datetime.utcnow() - timedelta(hours=48)).isoformat()
        recent_time = datetime.utcnow().isoformat()

        old_task = Task(agent_id="test", status=TaskStatus.COMPLETED)
        old_task.updated_at = old_time
        server._tasks[old_task.id] = old_task

        recent_task = Task(agent_id="test", status=TaskStatus.COMPLETED)
        recent_task.updated_at = recent_time
        server._tasks[recent_task.id] = recent_task

        working_task = Task(agent_id="test", status=TaskStatus.WORKING)
        working_task.updated_at = old_time
        server._tasks[working_task.id] = working_task

        cleared = server.clear_completed_tasks(max_age_hours=24)
        assert cleared == 1
        assert old_task.id not in server._tasks
        assert recent_task.id in server._tasks
        assert working_task.id in server._tasks

    def test_clear_completed_tasks_invalid_date(self, server: A2AServer) -> None:
        task = Task(agent_id="test", status=TaskStatus.FAILED)
        task.updated_at = "not-a-date"
        server._tasks[task.id] = task

        cleared = server.clear_completed_tasks(max_age_hours=24)
        assert cleared == 1


# ---------------------------------------------------------------------------
# A2AClient Tests
# ---------------------------------------------------------------------------


class TestA2AClientInit:
    """Tests for A2AClient initialization."""

    def test_init_strips_trailing_slash(self) -> None:
        client = A2AClient("https://example.com/")
        assert client.base_url == "https://example.com"

    def test_init_no_trailing_slash(self) -> None:
        client = A2AClient("https://example.com")
        assert client.base_url == "https://example.com"

    def test_init_agent_card_none(self) -> None:
        client = A2AClient("https://example.com")
        assert client.agent_card is None

    def test_init_with_agent_card(self, sample_card: AgentCard) -> None:
        client = A2AClient("https://example.com", agent_card=sample_card)
        assert client.agent_card is not None
        assert client.agent_card.name == "WeatherAgent"


class TestA2AClientError:
    """Tests for A2AClientError."""

    def test_error_with_code(self) -> None:
        err = A2AClientError("something failed", code=-32601)
        assert str(err) == "something failed"
        assert err.code == -32601

    def test_error_without_code(self) -> None:
        err = A2AClientError("generic error")
        assert err.code is None


class TestA2AClientDiscover:
    """Tests for A2AClient.discover_agent."""

    @pytest.mark.asyncio
    async def test_discover_agent_success(self, client: A2AClient) -> None:
        card_data = {
            "id": "remote-agent",
            "name": "RemoteAgent",
            "description": "A remote agent",
            "version": "1.0.0",
            "capabilities": [],
            "endpoints": {},
            "metadata": {},
            "created_at": datetime.utcnow().isoformat(),
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(card_data).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch(
            "agentforge.comms.a2a_client.urllib.request.urlopen", return_value=mock_response
        ):
            card = await client.discover_agent()

        assert card.id == "remote-agent"
        assert card.name == "RemoteAgent"
        assert client.agent_card is not None

    @pytest.mark.asyncio
    async def test_discover_agent_http_error(self, client: A2AClient) -> None:
        http_err = urllib.error.HTTPError(
            url="https://example.com/.well-known/agent.json",
            code=404,
            msg="Not Found",
            hdrs=None,  # type: ignore[arg-type]
            fp=None,
        )
        with (
            patch(
                "agentforge.comms.a2a_client.urllib.request.urlopen",
                side_effect=http_err,
            ),
            pytest.raises(A2AClientError, match="HTTP 404"),
        ):
            await client.discover_agent()

    @pytest.mark.asyncio
    async def test_discover_agent_url_error(self, client: A2AClient) -> None:
        url_err = urllib.error.URLError("Connection refused")
        with (
            patch(
                "agentforge.comms.a2a_client.urllib.request.urlopen",
                side_effect=url_err,
            ),
            pytest.raises(A2AClientError, match="Connection refused"),
        ):
            await client.discover_agent()

    @pytest.mark.asyncio
    async def test_discover_agent_invalid_json(self, client: A2AClient) -> None:
        mock_response = MagicMock()
        mock_response.read.return_value = b"not json"
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with (
            patch("agentforge.comms.a2a_client.urllib.request.urlopen", return_value=mock_response),
            pytest.raises(A2AClientError, match="Invalid agent card JSON"),
        ):
            await client.discover_agent()


class TestA2AClientSendTask:
    """Tests for A2AClient.send_task."""

    @pytest.mark.asyncio
    async def test_send_task_success(self, client: A2AClient) -> None:
        task_result = Task(
            agent_id="remote",
            status=TaskStatus.COMPLETED,
            output={"forecast": "Sunny"},
        )
        response_data = {
            "jsonrpc": "2.0",
            "result": task_result.model_dump(),
            "id": None,
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch(
            "agentforge.comms.a2a_client.urllib.request.urlopen", return_value=mock_response
        ):
            task = await client.send_task("get_forecast", {"location": "NYC"})

        assert task.status == TaskStatus.COMPLETED
        assert task.output == {"forecast": "Sunny"}

    @pytest.mark.asyncio
    async def test_send_task_error_response(self, client: A2AClient) -> None:
        response_data = {
            "jsonrpc": "2.0",
            "error": {"code": -32002, "message": "Capability not found"},
            "id": None,
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with (
            patch("agentforge.comms.a2a_client.urllib.request.urlopen", return_value=mock_response),
            pytest.raises(A2AClientError, match="Capability not found"),
        ):
            await client.send_task("nonexistent", {})


class TestA2AClientGetTask:
    """Tests for A2AClient.get_task."""

    @pytest.mark.asyncio
    async def test_get_task_success(self, client: A2AClient) -> None:
        task_data = Task(agent_id="test", status=TaskStatus.WORKING).model_dump()
        response_data = {"jsonrpc": "2.0", "result": task_data, "id": None}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch(
            "agentforge.comms.a2a_client.urllib.request.urlopen", return_value=mock_response
        ):
            task = await client.get_task("task-123")

        assert task.status == TaskStatus.WORKING

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, client: A2AClient) -> None:
        response_data = {
            "jsonrpc": "2.0",
            "error": {"code": -32001, "message": "Task not found"},
            "id": None,
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with (
            patch("agentforge.comms.a2a_client.urllib.request.urlopen", return_value=mock_response),
            pytest.raises(A2AClientError, match="Task not found"),
        ):
            await client.get_task("missing-task")


class TestA2AClientCancelTask:
    """Tests for A2AClient.cancel_task."""

    @pytest.mark.asyncio
    async def test_cancel_task_success(self, client: A2AClient) -> None:
        task_data = Task(agent_id="test", status=TaskStatus.CANCELLED).model_dump()
        response_data = {"jsonrpc": "2.0", "result": task_data, "id": None}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch(
            "agentforge.comms.a2a_client.urllib.request.urlopen", return_value=mock_response
        ):
            task = await client.cancel_task("task-to-cancel")

        assert task.status == TaskStatus.CANCELLED


class TestA2AClientListTasks:
    """Tests for A2AClient.list_tasks."""

    @pytest.mark.asyncio
    async def test_list_tasks_success(self, client: A2AClient) -> None:
        tasks = [Task(agent_id="test").model_dump() for _ in range(3)]
        response_data = {
            "jsonrpc": "2.0",
            "result": {"tasks": tasks, "total": 3},
            "id": None,
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch(
            "agentforge.comms.a2a_client.urllib.request.urlopen", return_value=mock_response
        ):
            result_tasks, total = await client.list_tasks()

        assert len(result_tasks) == 3
        assert total == 3

    @pytest.mark.asyncio
    async def test_list_tasks_with_status_filter(self, client: A2AClient) -> None:
        response_data = {
            "jsonrpc": "2.0",
            "result": {"tasks": [], "total": 0},
            "id": None,
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch(
            "agentforge.comms.a2a_client.urllib.request.urlopen", return_value=mock_response
        ):
            result_tasks, total = await client.list_tasks(status="completed", limit=10)

        assert result_tasks == []
        assert total == 0


class TestA2AClientGetAgentCard:
    """Tests for A2AClient.get_agent_card via JSON-RPC."""

    @pytest.mark.asyncio
    async def test_get_agent_card_success(self, client: A2AClient) -> None:
        card_data = AgentCard(id="remote", name="Remote", description="desc").model_dump()
        response_data = {"jsonrpc": "2.0", "result": card_data, "id": None}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch(
            "agentforge.comms.a2a_client.urllib.request.urlopen", return_value=mock_response
        ):
            card = await client.get_agent_card()

        assert card.id == "remote"
        assert card.name == "Remote"


class TestA2AClientPollTask:
    """Tests for A2AClient.poll_task_until_complete."""

    @pytest.mark.asyncio
    async def test_poll_completes(self, client: A2AClient) -> None:
        """Test polling returns when task completes."""
        completed_task = Task(agent_id="test", status=TaskStatus.COMPLETED)
        task_data = completed_task.model_dump()
        response_data = {"jsonrpc": "2.0", "result": task_data, "id": None}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch(
            "agentforge.comms.a2a_client.urllib.request.urlopen", return_value=mock_response
        ):
            task = await client.poll_task_until_complete("task-1", poll_interval=0.01, max_wait=1.0)

        assert task.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_poll_failed_task(self, client: A2AClient) -> None:
        """Test polling returns when task fails."""
        failed_task = Task(agent_id="test", status=TaskStatus.FAILED, error="boom")
        task_data = failed_task.model_dump()
        response_data = {"jsonrpc": "2.0", "result": task_data, "id": None}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch(
            "agentforge.comms.a2a_client.urllib.request.urlopen", return_value=mock_response
        ):
            task = await client.poll_task_until_complete("task-1", poll_interval=0.01, max_wait=1.0)

        assert task.status == TaskStatus.FAILED

    @pytest.mark.asyncio
    async def test_poll_timeout(self, client: A2AClient) -> None:
        """Test polling raises TimeoutError when max_wait exceeded."""
        working_task = Task(agent_id="test", status=TaskStatus.WORKING)
        task_data = working_task.model_dump()
        response_data = {"jsonrpc": "2.0", "result": task_data, "id": None}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with (
            patch("agentforge.comms.a2a_client.urllib.request.urlopen", return_value=mock_response),
            pytest.raises(asyncio.TimeoutError, match="did not complete"),
        ):
            await client.poll_task_until_complete("task-stuck", poll_interval=0.01, max_wait=0.05)


class TestA2AClientSendMessage:
    """Tests for A2AClient._send_message error handling."""

    @pytest.mark.asyncio
    async def test_send_message_http_error_with_json_body(self, client: A2AClient) -> None:
        error_body = json.dumps({"error": {"code": -32603, "message": "Internal"}}).encode()
        http_err = urllib.error.HTTPError(
            url="https://example.com/a2a",
            code=500,
            msg="Internal Server Error",
            hdrs=None,  # type: ignore[arg-type]
            fp=None,
        )
        http_err.read = MagicMock(return_value=error_body)

        with patch(
            "agentforge.comms.a2a_client.urllib.request.urlopen",
            side_effect=http_err,
        ):
            msg = A2AMessage(method="tasks/send", params={})
            resp = await client._send_message(msg)

        assert resp.error is not None
        assert resp.error["code"] == -32603

    @pytest.mark.asyncio
    async def test_send_message_http_error_non_json_body(self, client: A2AClient) -> None:
        http_err = urllib.error.HTTPError(
            url="https://example.com/a2a",
            code=502,
            msg="Bad Gateway",
            hdrs=None,  # type: ignore[arg-type]
            fp=None,
        )
        http_err.read = MagicMock(return_value=b"not json")

        with patch(
            "agentforge.comms.a2a_client.urllib.request.urlopen",
            side_effect=http_err,
        ):
            msg = A2AMessage(method="tasks/send", params={})
            resp = await client._send_message(msg)

        assert resp.error is not None
        assert resp.error["code"] == 502

    @pytest.mark.asyncio
    async def test_send_message_url_error(self, client: A2AClient) -> None:
        url_err = urllib.error.URLError("Connection refused")
        with patch(
            "agentforge.comms.a2a_client.urllib.request.urlopen",
            side_effect=url_err,
        ):
            msg = A2AMessage(method="tasks/send", params={})
            resp = await client._send_message(msg)

        assert resp.error is not None
        assert "Connection failed" in resp.error["message"]

    @pytest.mark.asyncio
    async def test_send_message_invalid_json_response(self, client: A2AClient) -> None:
        mock_response = MagicMock()
        mock_response.read.return_value = b"not valid json"
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch(
            "agentforge.comms.a2a_client.urllib.request.urlopen", return_value=mock_response
        ):
            msg = A2AMessage(method="tasks/send", params={})
            resp = await client._send_message(msg)

        assert resp.error is not None
        assert "Invalid JSON response" in resp.error["message"]


# ---------------------------------------------------------------------------
# A2ABridge Tests
# ---------------------------------------------------------------------------


class TestA2ABridgeAgentToCard:
    """Tests for A2ABridge.agent_to_card."""

    def _make_agent(
        self,
        agent_id: str = "test-agent",
        name: str = "TestAgent",
        description: str = "A test agent",
        tools: list[Any] | None = None,
    ) -> MagicMock:
        """Create a mock BaseAgent."""
        agent = MagicMock()
        agent.agent_id = agent_id
        agent.config = MagicMock()
        agent.config.name = name
        agent.config.description = description
        agent.tools = tools or []
        return agent

    def test_agent_to_card_no_tools(self) -> None:
        agent = self._make_agent()
        card = A2ABridge.agent_to_card(agent, "https://example.com")

        assert card.id == "test-agent"
        assert card.name == "TestAgent"
        assert card.description == "A test agent"
        assert len(card.capabilities) == 1
        assert card.capabilities[0].name == "execute"
        assert card.endpoints["tasks"] == "/a2a"
        assert card.metadata["framework"] == "agentforge"
        assert card.metadata["base_url"] == "https://example.com"

    def test_agent_to_card_with_tools(self) -> None:
        tool = MagicMock()
        tool.name = "search"
        tool.description = "Search documents"
        tool.parameters_schema = {"type": "object", "properties": {"q": {"type": "string"}}}

        agent = self._make_agent(tools=[tool])
        card = A2ABridge.agent_to_card(agent, "https://example.com")

        assert len(card.capabilities) == 1
        assert card.capabilities[0].name == "search"
        assert card.capabilities[0].description == "Search documents"
        assert card.capabilities[0].input_schema["type"] == "object"

    def test_agent_to_card_tool_with_docstring(self) -> None:
        tool = MagicMock(spec=[])

        # Tool without .name, .description — falls through to __name__ and __doc__
        tool.__name__ = "analyze"
        tool.__doc__ = "Analyze data deeply"
        # Remove attributes that would be checked first
        assert not hasattr(tool, "name")
        assert not hasattr(tool, "description")
        assert not hasattr(tool, "parameters_schema")
        assert not hasattr(tool, "input_schema")
        assert not hasattr(tool, "args_schema")

        agent = self._make_agent(tools=[tool])
        card = A2ABridge.agent_to_card(agent, "https://example.com")

        assert card.capabilities[0].name == "analyze"
        assert card.capabilities[0].description == "Analyze data deeply"

    def test_agent_to_card_tool_with_args_schema(self) -> None:
        tool = MagicMock()
        tool.name = "compute"
        tool.description = "Compute results"
        # Remove parameters_schema and input_schema
        del tool.parameters_schema
        del tool.input_schema
        tool.args_schema = MagicMock()
        tool.args_schema.model_json_schema.return_value = {
            "type": "object",
            "properties": {"x": {"type": "number"}},
        }

        agent = self._make_agent(tools=[tool])
        card = A2ABridge.agent_to_card(agent, "https://example.com")

        assert card.capabilities[0].input_schema["properties"]["x"]["type"] == "number"

    def test_agent_to_card_no_config_uses_agent_id(self) -> None:
        agent = MagicMock()
        agent.agent_id = "fallback-id"
        agent.config = None
        agent.tools = []

        card = A2ABridge.agent_to_card(agent, "https://example.com")
        assert card.id == "fallback-id"

    def test_agent_to_card_no_config_with_instructions(self) -> None:
        agent = MagicMock()
        agent.agent_id = "instr-agent"
        agent.config = None
        agent.tools = []
        agent.instructions = "You are a helpful assistant"

        card = A2ABridge.agent_to_card(agent, "https://example.com")
        assert "helpful assistant" in card.capabilities[0].description


class TestA2ABridgeCreateServer:
    """Tests for A2ABridge.create_server."""

    def test_create_server(self) -> None:
        agent = MagicMock()
        agent.agent_id = "srv-agent"
        agent.config = MagicMock()
        agent.config.name = "ServerAgent"
        agent.config.description = "A server agent"
        agent.tools = []

        server = A2ABridge.create_server(agent, "https://example.com")

        assert isinstance(server, A2AServer)
        assert server.agent_card.name == "ServerAgent"
        # Should have registered handler for the default "execute" capability
        assert "execute" in server._task_handlers

    def test_create_server_with_custom_card(self) -> None:
        agent = MagicMock()
        agent.agent_id = "srv-agent"
        agent.config = MagicMock()
        agent.config.name = "Agent"
        agent.config.description = ""
        agent.tools = []

        custom_card = AgentCard(
            id="custom-id",
            name="CustomAgent",
            capabilities=[AgentCapability(name="custom_cap", description="Custom capability")],
        )
        server = A2ABridge.create_server(agent, "https://example.com", agent_card=custom_card)

        assert server.agent_card.name == "CustomAgent"
        assert "custom_cap" in server._task_handlers


class TestA2ABridgeCreateClient:
    """Tests for A2ABridge.create_client."""

    def test_create_client(self) -> None:
        client = A2ABridge.create_client("https://remote.example.com")
        assert isinstance(client, A2AClient)
        assert client.base_url == "https://remote.example.com"


class TestA2ABridgeCallRemoteAgent:
    """Tests for A2ABridge.call_remote_agent."""

    @pytest.mark.asyncio
    async def test_call_remote_agent_with_output(self) -> None:
        completed_task = Task(
            agent_id="remote",
            status=TaskStatus.COMPLETED,
            output={"answer": "42"},
        )
        response_data = {
            "jsonrpc": "2.0",
            "result": completed_task.model_dump(),
            "id": None,
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch(
            "agentforge.comms.a2a_client.urllib.request.urlopen", return_value=mock_response
        ):
            result = await A2ABridge.call_remote_agent(
                "https://remote.example.com",
                "compute",
                {"input": "data"},
            )

        assert result == {"answer": "42"}

    @pytest.mark.asyncio
    async def test_call_remote_agent_with_error(self) -> None:
        error_task = Task(
            agent_id="remote",
            status=TaskStatus.FAILED,
            error="Something went wrong",
        )
        response_data = {
            "jsonrpc": "2.0",
            "result": error_task.model_dump(),
            "id": None,
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch(
            "agentforge.comms.a2a_client.urllib.request.urlopen", return_value=mock_response
        ):
            result = await A2ABridge.call_remote_agent("https://remote.example.com", "compute", {})

        assert result == {"error": "Something went wrong"}

    @pytest.mark.asyncio
    async def test_call_remote_agent_status_only(self) -> None:
        task = Task(agent_id="remote", status=TaskStatus.WORKING)
        response_data = {
            "jsonrpc": "2.0",
            "result": task.model_dump(),
            "id": None,
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch(
            "agentforge.comms.a2a_client.urllib.request.urlopen", return_value=mock_response
        ):
            result = await A2ABridge.call_remote_agent(
                "https://remote.example.com", "long_task", {}
            )

        assert result == {"status": "working"}


# ---------------------------------------------------------------------------
# Integration Tests (Server <-> Direct calls, no network)
# ---------------------------------------------------------------------------


class TestServerIntegration:
    """Integration tests using A2AServer directly."""

    @pytest.mark.asyncio
    async def test_full_task_lifecycle(self) -> None:
        """Test create -> get -> complete -> list lifecycle."""
        card = AgentCard(
            id="lifecycle-agent",
            name="LifecycleAgent",
            capabilities=[AgentCapability(name="process", description="Process data")],
        )
        server = A2AServer(card)

        async def process_handler(data: dict[str, Any]) -> dict[str, Any]:
            return {"processed": True, "input_keys": list(data.keys())}

        server.register_capability_handler("process", process_handler)

        # 1. Send task
        send_msg = A2AMessage(
            method="tasks/send",
            params={"capability": "process", "input": {"key": "value"}},
            id="lc-1",
        )
        send_resp = await server.handle_message(send_msg)
        assert send_resp.error is None
        task_id = send_resp.result["id"]
        assert send_resp.result["status"] == "completed"
        assert send_resp.result["output"]["processed"] is True

        # 2. Get task
        get_msg = A2AMessage(
            method="tasks/get",
            params={"task_id": task_id},
            id="lc-2",
        )
        get_resp = await server.handle_message(get_msg)
        assert get_resp.result["id"] == task_id

        # 3. List tasks
        list_msg = A2AMessage(method="tasks/list", params={}, id="lc-3")
        list_resp = await server.handle_message(list_msg)
        assert list_resp.result["total"] == 1

    @pytest.mark.asyncio
    async def test_multiple_capabilities(self) -> None:
        """Test server with multiple capabilities."""
        card = AgentCard(
            id="multi-agent",
            name="MultiAgent",
            capabilities=[
                AgentCapability(name="search", description="Search"),
                AgentCapability(name="analyze", description="Analyze"),
            ],
        )
        server = A2AServer(card)

        async def search_handler(data: dict[str, Any]) -> dict[str, Any]:
            return {"results": [f"result for {data.get('q', '')}"]}

        async def analyze_handler(data: dict[str, Any]) -> dict[str, Any]:
            return {"analysis": "positive"}

        server.register_capability_handler("search", search_handler)
        server.register_capability_handler("analyze", analyze_handler)

        # Search
        msg1 = A2AMessage(
            method="tasks/send",
            params={"capability": "search", "input": {"q": "test"}},
            id="m-1",
        )
        resp1 = await server.handle_message(msg1)
        assert resp1.result["output"]["results"] == ["result for test"]

        # Analyze
        msg2 = A2AMessage(
            method="tasks/send",
            params={"capability": "analyze", "input": {"text": "great!"}},
            id="m-2",
        )
        resp2 = await server.handle_message(msg2)
        assert resp2.result["output"]["analysis"] == "positive"

        # Both tasks stored
        assert len(server._tasks) == 2
