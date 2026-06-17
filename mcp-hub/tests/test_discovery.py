"""Tests for Discovery — manifest loading, fallback, error isolation."""

import tempfile
from pathlib import Path

import pytest
import yaml

from src.lifecycle.base_server import BaseMCPServer
from src.loader.discovery import Discovery, DiscoveryError, DiscoveryResult


# ── Test servers ──────────────────────────────────────────────


class _GoodServer(BaseMCPServer):
    def __init__(self, name="good", version="1.0"):
        super().__init__(name=name, version=version)

    async def initialize(self) -> None:
        pass

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass


class _FallbackServer(BaseMCPServer):
    def __init__(self, name="fallback", version="2.0"):
        super().__init__(name=name, version=version)

    async def initialize(self) -> None:
        pass

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass


# ── Helpers ──────────────────────────────────────────────────


def _write_manifest(directory: Path, data: dict) -> None:
    with open(directory / "manifest.yaml", "w") as f:
        yaml.dump(data, f)


def _write_server_py(directory: Path, class_name: str, import_line: str = "") -> None:
    content = f'''
import sys
sys.path.insert(0, r"C:/Users/victor/ai-infrastructure/mcp-hub")
{import_line}
from src.lifecycle.base_server import BaseMCPServer

class {class_name}(BaseMCPServer):
    def __init__(self, name=None, version="0.1.0"):
        super().__init__(name=name or "{class_name.lower()}", version=version)
    async def initialize(self) -> None: pass
    async def start(self) -> None: pass
    async def stop(self) -> None: pass
'''
    with open(directory / "server.py", "w") as f:
        f.write(content)


# ── Manifest success ─────────────────────────────────────────


class TestManifestSuccess:
    async def test_loads_server_via_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            srv_dir = tmpdir / "good_plugin"
            srv_dir.mkdir()
            _write_manifest(srv_dir, {"name": "good_plugin", "version": "1.0", "class": "GoodServer"})
            _write_server_py(srv_dir, "GoodServer")

            discovery = Discovery(base_path=str(tmpdir))
            servers, result = await discovery.discover()

            assert len(servers) == 1
            assert servers[0].name == "good_plugin"
            assert servers[0].version == "1.0"
            assert result.loaded == ["good_plugin"]
            assert result.failed == []


# ── Fallback success ─────────────────────────────────────────


class TestFallbackSuccess:
    async def test_loads_server_without_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            srv_dir = tmpdir / "fallback_plugin"
            srv_dir.mkdir()
            _write_server_py(srv_dir, "FallbackPlugin")

            discovery = Discovery(base_path=str(tmpdir))
            servers, result = await discovery.discover()

            assert len(servers) == 1
            assert servers[0].name == "fallbackplugin"
            assert result.loaded == ["fallbackplugin"]


# ── Missing manifest.yaml (not an error — fallback) ─────────


class TestMissingManifest:
    async def test_missing_manifest_falls_back_to_module(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            srv_dir = tmpdir / "no_manifest"
            srv_dir.mkdir()
            _write_server_py(srv_dir, "NoManifestServer")

            discovery = Discovery(base_path=str(tmpdir))
            servers, result = await discovery.discover()

            assert len(servers) == 1
            assert result.loaded == ["no_manifest"]


# ── Missing server.py ────────────────────────────────────────


class TestMissingServerPy:
    async def test_manifest_without_server_py_fails_cleanly(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            srv_dir = tmpdir / "bad_plugin"
            srv_dir.mkdir()
            _write_manifest(srv_dir, {"name": "bad_plugin", "class": "BadServer"})
            # No server.py

            discovery = Discovery(base_path=str(tmpdir))
            servers, result = await discovery.discover()

            assert len(servers) == 0
            assert len(result.failed) == 1
            assert result.failed[0][0] == "bad_plugin"


# ── Import failure ───────────────────────────────────────────


class TestImportFailure:
    async def test_broken_server_py_does_not_crash_hub(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            srv_dir = tmpdir / "broken_plugin"
            srv_dir.mkdir()
            _write_manifest(srv_dir, {"name": "broken", "class": "BrokenServer"})
            # Write a server.py with a syntax error
            with open(srv_dir / "server.py", "w") as f:
                f.write("this is not valid python {{{")

            discovery = Discovery(base_path=str(tmpdir))
            servers, result = await discovery.discover()

            assert len(servers) == 0
            assert len(result.failed) == 1
            assert result.failed[0][0] == "broken_plugin"


# ── Error isolation — one bad server doesn't block others ───


class TestErrorIsolation:
    async def test_bad_plugin_does_not_block_good_plugin(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            # Good plugin
            good_dir = tmpdir / "good"
            good_dir.mkdir()
            _write_manifest(good_dir, {"name": "good", "class": "GoodServer"})
            _write_server_py(good_dir, "GoodServer")

            # Bad plugin
            bad_dir = tmpdir / "bad"
            bad_dir.mkdir()
            _write_manifest(bad_dir, {"name": "bad", "class": "BadServer"})
            with open(bad_dir / "server.py", "w") as f:
                f.write("syntax error {{{")

            discovery = Discovery(base_path=str(tmpdir))
            servers, result = await discovery.discover()

            assert len(servers) == 1
            assert servers[0].name == "good"
            assert result.loaded == ["good"]
            assert len(result.failed) == 1
            assert result.failed[0][0] == "bad"


# ── Empty namespace ──────────────────────────────────────────


class TestEmptyNamespace:
    async def test_empty_directory_returns_no_servers(self):
        with tempfile.TemporaryDirectory() as tmp:
            discovery = Discovery(base_path=str(tmp))
            servers, result = await discovery.discover()
            assert servers == []
            assert result.loaded == []
            assert result.failed == []


# ── DiscoveryError ───────────────────────────────────────────


class TestDiscoveryError:
    def test_discovery_error_message(self):
        err = DiscoveryError("my_plugin", "something went wrong")
        assert "my_plugin" in str(err)
        assert "something went wrong" in str(err)
        assert err.server_dir == "my_plugin"
        assert err.reason == "something went wrong"


# ── DiscoveryResult ──────────────────────────────────────────


class TestDiscoveryResult:
    def test_empty_result(self):
        r = DiscoveryResult()
        assert r.loaded == []
        assert r.failed == []

    def test_successful_result(self):
        r = DiscoveryResult()
        r.loaded.append("example")
        assert len(r.loaded) == 1

    def test_failed_result(self):
        r = DiscoveryResult()
        r.failed.append(("bad", "parse error"))
        assert len(r.failed) == 1
        assert r.failed[0] == ("bad", "parse error")
