"""Tests for lifecycle — initialize(), lifecycle_start(), lifecycle_stop()."""

import pytest

from src.lifecycle.base_server import BaseMCPServer, ToolNotFoundError
from src.registry.server_manager import ServerManager


# ── Test servers ──────────────────────────────────────────────


class _LifecycleServer(BaseMCPServer):
    """Tracks lifecycle calls for assertions."""

    def __init__(self, name="lifecycle-test", version="0.1.0"):
        super().__init__(name=name, version=version)
        self.initialized = False
        self.started = False
        self.stopped = False

    async def initialize(self) -> None:
        self.initialized = True

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True


class _FailingInitServer(BaseMCPServer):
    def __init__(self, name="failing"):
        super().__init__(name=name)

    async def initialize(self) -> None:
        raise RuntimeError("init failure")

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass


class _FailingStartServer(BaseMCPServer):
    def __init__(self, name="failing-start"):
        super().__init__(name=name)

    async def initialize(self) -> None:
        pass

    async def start(self) -> None:
        raise RuntimeError("start failure")

    async def stop(self) -> None:
        pass


# ── Lifecycle: initialize + lifecycle_start ──────────────────


class TestLifecycleStart:
    async def test_initialize_called_before_start(self):
        srv = _LifecycleServer()
        mgr = ServerManager()
        mgr.register(srv)
        await mgr.start_all()

        assert srv.initialized is True
        assert srv.started is True
        assert srv.is_running is True  # lifecycle_start() manages _running

    async def test_running_true_after_lifecycle_start(self):
        srv = _LifecycleServer()
        assert srv.is_running is False
        await srv.initialize()
        await srv.lifecycle_start()
        assert srv.is_running is True

    async def test_lifecycle_start_logs(self, caplog):
        srv = _LifecycleServer()
        await srv.initialize()
        await srv.lifecycle_start()
        # Check _running was set by lifecycle_start, not by start()
        assert srv.is_running is True


# ── Lifecycle: lifecycle_stop ────────────────────────────────


class TestLifecycleStop:
    async def test_lifecycle_stop_sets_running_false(self):
        srv = _LifecycleServer()
        await srv.initialize()
        await srv.lifecycle_start()
        assert srv.is_running is True

        await srv.lifecycle_stop()
        assert srv.is_running is False
        assert srv.stopped is True

    async def test_stop_all_calls_lifecycle_stop(self):
        srv = _LifecycleServer()
        mgr = ServerManager()
        mgr.register(srv)
        await mgr.start_all()
        assert srv.is_running is True

        await mgr.stop_all()
        assert srv.is_running is False
        assert srv.stopped is True


# ── ServerManager does NOT touch _running directly ───────────


class TestNoDuplicateState:
    """ServerManager must not set _running — only lifecycle wrappers do."""

    async def test_start_all_does_not_set_running(self):
        """lifecycle_start() sets _running, not ServerManager."""
        srv = _LifecycleServer()
        mgr = ServerManager()
        mgr.register(srv)
        await mgr.start_all()
        assert srv.is_running is True  # set by lifecycle_start, not mgr

    async def test_stop_all_does_not_clear_running(self):
        """lifecycle_stop() clears _running, not ServerManager."""
        srv = _LifecycleServer()
        mgr = ServerManager()
        mgr.register(srv)
        await mgr.start_all()
        await mgr.stop_all()
        assert srv.is_running is False  # cleared by lifecycle_stop, not mgr


# ── Failure isolation ────────────────────────────────────────


class TestFailureIsolation:
    async def test_failing_init_isolated(self):
        mgr = ServerManager()
        mgr.register(_FailingInitServer())
        await mgr.start_all()
        assert mgr.failed_count == 1
        assert "failing" in mgr.failed_servers

    async def test_failing_start_isolated(self):
        mgr = ServerManager()
        mgr.register(_FailingStartServer())
        await mgr.start_all()
        assert mgr.failed_count == 1

    async def test_good_server_starts_when_other_fails(self):
        mgr = ServerManager()
        mgr.register(_LifecycleServer("good"))
        mgr.register(_FailingInitServer("bad"))
        await mgr.start_all()

        good = mgr.get_server("good")
        assert good.is_running is True
        assert mgr.running_count == 1
        assert mgr.failed_count == 1
        assert "bad" in mgr.failed_servers


# ── ServerManager stats ──────────────────────────────────────


class TestServerManagerStats:
    async def test_counts(self):
        mgr = ServerManager()
        mgr.register(_LifecycleServer("one"))
        mgr.register(_LifecycleServer("two"))
        await mgr.start_all()

        assert mgr.count == 2
        assert mgr.running_count == 2
        assert mgr.failed_count == 0
        assert mgr.failed_servers == []

    async def test_list_servers_includes_failed_flag(self):
        mgr = ServerManager()
        mgr.register(_LifecycleServer("good"))
        mgr.register(_FailingInitServer("bad"))
        await mgr.start_all()

        servers = mgr.list_servers()
        assert len(servers) == 2
        good = [s for s in servers if s["name"] == "good"][0]
        bad = [s for s in servers if s["name"] == "bad"][0]
        assert good["running"] is True
        assert good["failed"] is False
        assert bad["running"] is False
        assert bad["failed"] is True
