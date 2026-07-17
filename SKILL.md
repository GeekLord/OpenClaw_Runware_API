---
name: runware-mcp
version: 2.0.0
author: Shobhit Kumar Prabhakar
description: Generate images, videos, audio, text, and 3D models via the Runware.ai MCP server and official Python SDK. Handles multi-modal generation, model browsing, pricing lookup, and account management.
---

# Runware MCP Skill

A modern, multi-modal skill for generating media via [Runware.ai](https://runware.ai) using the official `runware-sdk` Python library.

## What's New in v2.0

- **Multi-modal** — image, video, audio, text, and 3D generation from one script
- **Official SDK** — uses `runware-sdk` (async, typed, validated) instead of raw REST
- **MCP integration** — new `scripts/runware_mcp.py` exposes MCP-style tools (`run`, `list-models`, `model-pricing`, `model-details`, `account`)
- **Better defaults** — sensible model picks per mode, configurable via CLI
- **Python 3.11+** — requires modern Python for full async SDK support

## Files

| File | Purpose |
|------|---------|
| `scripts/generate.py` | Main multi-modal generator (CLI) |
| `scripts/runware_mcp.py` | MCP-style tool interface (CLI) |
| `skill-config.json` | Default settings (no secrets) |
| `tests/test_generate.py` | Pytest unit tests for the generator |

## Prerequisites

- **Python 3.11+**
- **Runware API key** — get one at [runware.ai](https://runware.ai)
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

## Quick Start

Set your API key in `.env` or the environment:

```bash
echo "RUNWARE_API_KEY=your_key_here" > .env
```

### Generate an image

```bash
python scripts/generate.py --prompt "A mountain landscape at sunset" --mode image --outfile sunset.png
```

### Generate a video

```bash
python scripts/generate.py --prompt "Waves crashing on a beach" --mode video --duration 8 --outfile beach.mp4
```

### Generate text

```bash
python scripts/generate.py --prompt "Write a haiku about AI" --mode text --outfile haiku.txt
```

### MCP-style: list models

```bash
python scripts/runware_mcp.py list-models --category image --search "flux"
```

### MCP-style: get pricing

```bash
python scripts/runware_mcp.py model-pricing --model "runware:101@1"
```

### MCP-style: check account balance

```bash
python scripts/runware_mcp.py account
```

## Usage Notes

### CLI flags for `generate.py`

| Flag | Description |
|------|-------------|
| `--prompt` | Text prompt (required unless mode=text with default prompt) |
| `--mode` | One of: `image`, `video`, `audio`, `text`, `3d` |
| `--model` | Runware model ID (e.g. `runware:400@1`, `klingai:kling-video@3-4k`) |
| `--size` | Dimensions: `1024x1024` |
| `--sync` / `--no-sync` | Sync delivery (default) vs async polling |
| `--duration` | Video duration in seconds |
| `--num-results` | Number of results to generate |
| `--extra KEY VALUE` | Extra payload parameters (repeatable) |
| `--outfile` | Output filename |

## Safety

The skill includes a lightweight prompt filter to block prompts referencing minors.
This is a basic safeguard — users must follow Runware's content policy.

## MCP Server Connection

To connect this skill as an MCP server in any MCP-compatible client:

1. **Hosted server** (easiest — no setup):
   ```json
   {
     "mcpServers": {
       "runware": {
         "url": "https://mcp.runware.ai"
       }
     }
   }
   ```
   This connects directly to Runware's hosted MCP server at `mcp.runware.ai`.
   Authentication is handled via OAuth 2.1 — your API key stays server-side.

2. **Local stdio server** (self-hosted):
   ```json
   {
     "mcpServers": {
       "runware": {
         "command": "npx",
         "args": ["-y", "@runware/mcp"],
         "env": {
           "RUNWARE_API_KEY": "your-api-key"
         }
       }
     }
   }
   ```
   The official `@runware/mcp` package exposes the same tool set.

3. **via runware-sdk** (Python, this skill):
   ```json
   {
     "mcpServers": {
       "runware-python": {
         "command": "python",
         "args": ["scripts/runware_mcp.py"]
       }
     }
   }
   ```

Tools exposed by the MCP server:
- **run** — execute any Runware inference task
- **list_models** — browse the curated model catalog
- **model_pricing** — get pricing for a model
- **model_details** — full metadata for a model
- **account** — account info and balance
- **model_schema** — fetch the parameter schema for a model
- **get_task_details** — look up a previous task

## Integration with OpenClaw

This skill is compatible with OpenClaw's skill system. After installing dependencies,
an OpenClaw agent can invoke:

```python
# Example agent action:
python scripts/generate.py --prompt "cat portrait" --mode image
```

The agent will automatically:
1. Load the API key from `.env`
2. Choose the right model and parameters
3. Generate and save the result

## Testing

```bash
pytest -q
```

Integration tests require `RUNWARE_API_KEY` set in the environment.

## Migration from v1.x

If you were using the old `generate_image.py` (raw REST API):

- Run `pip install runware-sdk` to get the new SDK
- Replace `scripts/generate_image.py` with `scripts/generate.py`
- All v1 CLI flags (`--prompt`, `--outfile`, `--size`, `--model`, `--num-results`, `--sync`) still work
- New: `--mode` flag, `--extra`, `--duration`
- The SDK handles sync/async delivery, schema validation, error codes
- New MCP-style `scripts/runware_mcp.py` for tool-oriented usage
