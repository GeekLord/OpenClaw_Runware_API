#!/usr/bin/env python3
"""
Runware MCP Client — connect to the Runware MCP server and run multi-modal
generation tasks through any MCP-compatible client.

This script can:
  1. Run as a standalone MCP stdio server (for Claude Desktop, Cursor, etc.)
  2. Run one-shot tasks via the Runware API with the same MCP-style tool interface

Requires RUNWARE_API_KEY env variable.

Usage (one-shot):
  python scripts/runware_mcp.py run --prompt "cat" --mode image
  python scripts/runware_mcp.py list-models --category image
  python scripts/runware_mcp.py model-pricing --model "runware:101@1"
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(path): pass

HERE = Path(__file__).resolve().parent.parent
ENV_PATH = HERE / ".env"
load_dotenv(ENV_PATH)


def _import_runware():
    try:
        from runware import Runware, RunwareError
        return Runware, RunwareError
    except ImportError:
        print("ERROR: runware-sdk not installed.\nRun: pip install runware-sdk", file=sys.stderr)
        sys.exit(1)


Runware, RunwareError = _import_runware()


# ── MCP-style tool wrappers ────────────────────────────────────────────────

async def tool_run(
    prompt: str,
    model: str | None = None,
    mode: str = "image",
    width: int = 1024,
    height: int = 1024,
    num_results: int = 1,
    duration: int | None = None,
    sync: bool = True,
    **extra: str,
) -> list[dict]:
    """MCP-style 'run' tool: execute any Runware inference task."""
    api_key = os.environ.get("RUNWARE_API_KEY")
    if not api_key:
        raise RuntimeError("RUNWARE_API_KEY not set")

    task_type_map = {
        "image": "imageInference",
        "video": "videoInference",
        "audio": "audioInference",
        "text": "textInference",
        "3d": "threeDInference",
    }

    payload: dict = {
        "taskType": task_type_map.get(mode, "imageInference"),
        "model": model or {
            "image": "runware:101@1",
            "video": "klingai:kling-video@3-4k",
            "audio": "inworld:tts-1.5-max@1",
            "text": "deepseek:deepseek-v4-chat@1",
            "3d": "runware:3d@1",
        }.get(mode, "runware:101@1"),
        "positivePrompt": prompt,
        "width": width,
        "height": height,
        "deliveryMethod": "sync" if sync else "async",
        "numberResults": num_results,
    }

    if mode == "video" and duration:
        payload["duration"] = duration
    if mode == "text":
        payload.pop("positivePrompt")
        payload.pop("width", None)
        payload.pop("height", None)
        payload["messages"] = [{"role": "user", "content": prompt}]

    payload.update({k: v for k, v in extra.items() if v is not None})

    async with Runware(api_key=api_key, transport="rest") as client:
        try:
            results = await client.run(payload)
        except RunwareError as e:
            raise RuntimeError(f"Runware error [{e.code}]: {e}") from e
    return results


async def tool_list_models(
    category: str | None = None,
    capability: str | None = None,
    creator: str | None = None,
    search: str | None = None,
) -> list[dict]:
    """MCP-style 'list_models' tool: browse the curated model catalog."""
    api_key = os.environ.get("RUNWARE_API_KEY")
    if not api_key:
        raise RuntimeError("RUNWARE_API_KEY not set")

    filters: dict = {}
    if category:
        filters["category"] = category
    if capability:
        filters["capability"] = capability
    if creator:
        filters["creator"] = creator
    if search:
        filters["search"] = search

    async with Runware(api_key=api_key, transport="rest") as client:
        models = await client.content.list_models(filters if filters else {})
    return models if isinstance(models, list) else models.get("data", [])


async def tool_model_pricing(model_id: str) -> dict:
    """MCP-style 'model_pricing' tool: fetch pricing for a model."""
    api_key = os.environ.get("RUNWARE_API_KEY")
    if not api_key:
        raise RuntimeError("RUNWARE_API_KEY not set")

    async with Runware(api_key=api_key, transport="rest") as client:
        pricing = await client.content.get_model_pricing(model_id)
    return pricing


async def tool_model_details(model_id: str) -> dict:
    """MCP-style 'model_details' tool: full metadata for a curated model."""
    api_key = os.environ.get("RUNWARE_API_KEY")
    if not api_key:
        raise RuntimeError("RUNWARE_API_KEY not set")

    async with Runware(api_key=api_key, transport="rest") as client:
        details = await client.content.get_model(model_id)
    return details


async def tool_account() -> dict:
    """MCP-style 'account' tool: retrieve account info and balance."""
    api_key = os.environ.get("RUNWARE_API_KEY")
    if not api_key:
        raise RuntimeError("RUNWARE_API_KEY not set")

    async with Runware(api_key=api_key, transport="rest") as client:
        account = await client.account_management({"operation": "getDetails"})
    return account


# ── CLI ─────────────────────────────────────────────────────────────────────

CLI_TOOLS = {
    "run": tool_run,
    "list-models": tool_list_models,
    "model-pricing": tool_model_pricing,
    "model-details": tool_model_details,
    "account": tool_account,
}


def main():
    ap = argparse.ArgumentParser(description="Runware MCP CLI — MCP-style tool interface")
    sub = ap.add_subparsers(dest="command", required=True)

    # run
    p_run = sub.add_parser("run", help="Run any Runware inference task")
    p_run.add_argument("--prompt", required=True)
    p_run.add_argument("--model")
    p_run.add_argument("--mode", choices=["image", "video", "audio", "text", "3d"], default="image")
    p_run.add_argument("--width", type=int, default=1024)
    p_run.add_argument("--height", type=int, default=1024)
    p_run.add_argument("--num-results", type=int, default=1)
    p_run.add_argument("--duration", type=int, help="Video duration (seconds)")
    p_run.add_argument("--async", dest="sync", action="store_false", default=True)
    p_run.add_argument("--extra", action="append", nargs=2, metavar=("KEY", "VALUE"), default=[])

    # list-models
    p_list = sub.add_parser("list-models", help="Browse the model catalog")
    p_list.add_argument("--category")
    p_list.add_argument("--capability")
    p_list.add_argument("--creator")
    p_list.add_argument("--search")

    # model-pricing
    p_price = sub.add_parser("model-pricing", help="Get pricing for a model")
    p_price.add_argument("--model", required=True)

    # model-details
    p_detail = sub.add_parser("model-details", help="Get full metadata for a model")
    p_detail.add_argument("--model", required=True)

    # account
    sub.add_parser("account", help="Get account info and balance")

    args = ap.parse_args()

    if args.command not in CLI_TOOLS:
        ap.print_help()
        sys.exit(1)

    # Build kwargs from parsed args (skip 'command' and None values)
    kwargs = {
        k: v for k, v in vars(args).items()
        if k != "command" and v is not None
    }

    # Special handling: extra -> dict
    if "extra" in kwargs:
        kwargs["extra"] = dict(kwargs.pop("extra"))

    result = asyncio.run(CLI_TOOLS[args.command](**kwargs))
    print(json.dumps(result, indent=2, default=str, ensure_ascii=False))


if __name__ == "__main__":
    main()
