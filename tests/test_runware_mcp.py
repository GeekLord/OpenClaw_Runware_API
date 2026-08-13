import asyncio
import json
import os
import sys
from pathlib import Path
import pytest

# Ensure the project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import runware_mcp as mcp


class TestMcpCliParser:
    def test_run_parser_defaults(self):
        parser = mcp.build_parser()
        args = parser.parse_args(["run", "--prompt", "sunset over mountains"])
        assert args.command == "run"
        assert args.prompt == "sunset over mountains"
        assert args.mode == "image"
        assert args.width == 1024
        assert args.height == 1024
        assert args.sync is True

    def test_run_parser_custom_options(self):
        parser = mcp.build_parser()
        args = parser.parse_args([
            "run",
            "--prompt", "cyberpunk street",
            "--mode", "video",
            "--width", "1280",
            "--height", "720",
            "--duration", "6",
            "--no-sync",
            "--extra", "CFGScale", "7.5",
        ])
        assert args.command == "run"
        assert args.mode == "video"
        assert args.width == 1280
        assert args.height == 720
        assert args.duration == 6
        assert args.sync is False
        assert args.extra == [["CFGScale", "7.5"]]

    def test_list_models_parser(self):
        parser = mcp.build_parser()
        args = parser.parse_args(["list-models", "--category", "image", "--search", "flux"])
        assert args.command == "list-models"
        assert args.category == "image"
        assert args.search == "flux"

    def test_model_pricing_parser(self):
        parser = mcp.build_parser()
        args = parser.parse_args(["model-pricing", "--model", "runware:101@1"])
        assert args.command == "model-pricing"
        assert args.model == "runware:101@1"

    def test_model_details_parser(self):
        parser = mcp.build_parser()
        args = parser.parse_args(["model-details", "--model", "runware:101@1"])
        assert args.command == "model-details"
        assert args.model == "runware:101@1"

    def test_account_parser(self):
        parser = mcp.build_parser()
        args = parser.parse_args(["account"])
        assert args.command == "account"


def test_tool_run_requires_api_key(monkeypatch):
    monkeypatch.delenv("RUNWARE_API_KEY", raising=False)
    # Mock _import_runware so we test key check logic directly
    monkeypatch.setattr(mcp, "_import_runware", lambda: (object, Exception))
    with pytest.raises(RuntimeError, match="RUNWARE_API_KEY not set"):
        asyncio.run(mcp.tool_run(prompt="test prompt"))
