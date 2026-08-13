#!/usr/bin/env python3
"""
Runware MCP client: connect to Runware services and run multi-modal
generation tasks through an MCP-style tool interface.

This script supports:
  1. Running as an MCP tool interface
  2. Running one-shot tasks with the Runware API

Usage:
  python scripts/runware_mcp.py run --prompt "cat" --mode image
  python scripts/runware_mcp.py list-models --category image
  python scripts/runware_mcp.py model-pricing --model "runware:101@1"

Requires the RUNWARE_API_KEY environment variable.
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
    def load_dotenv(path):
        pass

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


# MCP-style tool wrappers

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
    """Execute any Runware inference task."""
    Runware, RunwareError = _import_runware()

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

    default_models = {
        "image": "runware:101@1",
        "video": "klingai:kling-video@3-4k",
        "audio": "inworld:tts-1.5-max@1",
        "text": "deepseek:deepseek-v4-chat@1",
        "3d": "runware:3d@1",
    }

    payload: dict = {
        "taskType": task_type_map.get(mode, "imageInference"),
        "model": model or default_models.get(mode, "runware:101@1"),
        "positivePrompt": prompt,
        "width": width,
        "height": height,
        "deliveryMethod": "sync" if sync else "async",
        "numberResults": num_results,
    }

    if mode == "video" and duration:
        payload["duration"] = duration
    if mode == "text":
        payload.pop("positivePrompt", None)
        payload.pop("width", None)
        payload.pop("height", None)
        payload["messages"] = [{"role": "user", "content": prompt}]

    for k, v in extra.items():
        if v is not None:
            try:
                v = json.loads(v)
            except (json.JSONDecodeError, TypeError):
                pass
            payload[k] = v

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
    """Browse the model catalog."""
    Runware, _ = _import_runware()

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
    """Fetch pricing for a given model."""
    Runware, _ = _import_runware()

    api_key = os.environ.get("RUNWARE_API_KEY")
    if not api_key:
        raise RuntimeError("RUNWARE_API_KEY not set")

    async with Runware(api_key=api_key, transport="rest") as client:
        pricing = await client.content.get_model_pricing(model_id)
    return pricing


async def tool_model_details(model_id: str) -> dict:
    """Fetch metadata for a given model."""
    Runware, _ = _import_runware()

    api_key = os.environ.get("RUNWARE_API_KEY")
    if not api_key:
        raise RuntimeError("RUNWARE_API_KEY not set")

    async with Runware(api_key=api_key, transport="rest") as client:
        details = await client.content.get_model(model_id)
    return details


async def tool_account() -> dict:
    """Retrieve account details and current balance."""
    Runware, _ = _import_runware()

    api_key = os.environ.get("RUNWARE_API_KEY")
    if not api_key:
        raise RuntimeError("RUNWARE_API_KEY not set")

    async with Runware(api_key=api_key, transport="rest") as client:
        account = await client.account_management({"operation": "getDetails"})
    return account


# CLI routing

CLI_TOOLS = {
    "run": tool_run,
    "list-models": tool_list_models,
    "model-pricing": tool_model_pricing,
    "model-details": tool_model_details,
    "account": tool_account,
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Runware MCP command-line tool interface")
    sub = ap.add_subparsers(dest="command", required=True)

    # run command
    p_run = sub.add_parser("run", help="Run any Runware inference task")
    p_run.add_argument("--prompt", required=True, help="Text prompt for generation")
    p_run.add_argument("--model", help="Runware model ID")
    p_run.add_argument(
        "--mode",
        choices=["image", "video", "audio", "text", "3d"],
        default="image",
        help="Inference mode (default: image)",
    )
    p_run.add_argument("--width", type=int, default=1024, help="Width in pixels")
    p_run.add_argument("--height", type=int, default=1024, help="Height in pixels")
    p_run.add_argument("--num-results", type=int, default=1, help="Number of results")
    p_run.add_argument("--duration", type=int, help="Video duration in seconds")
    p_run.add_argument(
        "--no-sync",
        "--async",
        dest="sync",
        action="store_false",
        default=True,
        help="Use async delivery with polling",
    )
    p_run.add_argument(
        "--extra",
        action="append",
        nargs=2,
        metavar=("KEY", "VALUE"),
        default=[],
        help="Extra payload key-value pairs (repeatable)",
    )

    # list-models command
    p_list = sub.add_parser("list-models", help="Browse the model catalog")
    p_list.add_argument("--category", help="Model category filter")
    p_list.add_argument("--capability", help="Capability filter")
    p_list.add_argument("--creator", help="Creator filter")
    p_list.add_argument("--search", help="Search query")

    # model-pricing command
    p_price = sub.add_parser("model-pricing", help="Get pricing for a model")
    p_price.add_argument("--model", required=True, help="Model ID")

    # model-details command
    p_detail = sub.add_parser("model-details", help="Get metadata for a model")
    p_detail.add_argument("--model", required=True, help="Model ID")

    # account command
    sub.add_parser("account", help="Get account info and balance")

    return ap


def main():
    ap = build_parser()
    args = ap.parse_args()

    if args.command not in CLI_TOOLS:
        ap.print_help()
        sys.exit(1)

    # Build kwargs from parsed args (skip 'command' and None values)
    kwargs = {
        k: v for k, v in vars(args).items()
        if k != "command" and v is not None
    }

    # Special handling: convert extra list of pairs into dictionary
    if "extra" in kwargs:
        kwargs["extra"] = dict(kwargs.pop("extra"))

    result = asyncio.run(CLI_TOOLS[args.command](**kwargs))
    print(json.dumps(result, indent=2, default=str, ensure_ascii=False))


if __name__ == "__main__":
    main()
