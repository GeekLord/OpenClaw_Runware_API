---
name: runware-mcp
version: 2.0.0
author: Shobhit Kumar Prabhakar
description: Generate images, videos, audio, text, and 3D models via the Runware.ai MCP server and official Python SDK. Handles multi-modal generation, model browsing, pricing lookup, and account management.
---

# Runware MCP skill

A skill for generating media through [Runware.ai](https://runware.ai) using the official `runware-sdk` Python library.

## What is new in v2.0

- Media generation across images, videos, audio, text, and 3D models
- Asynchronous SDK execution with typed payload validation
- Dedicated MCP tool CLI (`scripts/runware_mcp.py`) supporting `run`, `list-models`, `model-pricing`, `model-details`, and `account`
- Default model selections configured per modality
- Modern Python runtime requirement (Python 3.11+)

## Files

| File | Purpose |
|------|---------|
| `scripts/generate.py` | CLI generator for all supported modalities |
| `scripts/runware_mcp.py` | MCP tool CLI interface |
| `skill-config.json` | Default configuration settings |
| `tests/test_generate.py` | Tests for generation and file saving logic |
| `tests/test_runware_mcp.py` | Tests for MCP tool routing and parser arguments |

## Prerequisites

- Python 3.11 or higher
- A Runware API key from [runware.ai](https://runware.ai)
- Dependencies installed via:
  ```bash
  pip install -r requirements.txt
  ```

## Quick start

Set your API key in `.env` or in your environment:

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

### List models with MCP CLI

```bash
python scripts/runware_mcp.py list-models --category image --search "flux"
```

### Look up model pricing

```bash
python scripts/runware_mcp.py model-pricing --model "runware:101@1"
```

### Check account balance

```bash
python scripts/runware_mcp.py account
```

## Usage notes

### CLI flags for `generate.py`

| Flag | Description |
|------|-------------|
| `--prompt` | Text prompt (required for non-text modes) |
| `--mode` | One of: `image`, `video`, `audio`, `text`, `3d` |
| `--model` | Runware model ID (e.g. `runware:400@1`, `klingai:kling-video@3-4k`) |
| `--size` | Dimensions (e.g. `1024x1024`) |
| `--sync` / `--no-sync` | Synchronous delivery (default) versus asynchronous polling |
| `--duration` | Video duration in seconds |
| `--num-results` | Number of results to generate |
| `--extra KEY VALUE` | Extra payload parameters (repeatable) |
| `--outfile` | Output file path |

## Safety

The generator includes a local prompt filter to block requests referencing minors. Prompts must also comply with Runware content policies.

## MCP server connection

You can connect to Runware MCP tooling through three methods:

1. Hosted server endpoint:
   ```json
   {
     "mcpServers": {
       "runware": {
         "url": "https://mcp.runware.ai"
       }
     }
   }
   ```
   Connects directly to the hosted server at `mcp.runware.ai` using OAuth 2.1 authentication.

2. Local stdio server via npm:
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

3. Local Python script:
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

Available MCP tools:
- `run`: execute an inference task across any supported modality
- `list_models`: browse the curated model catalog
- `model_pricing`: check pricing for a model
- `model_details`: view model metadata and configuration options
- `account`: retrieve account details and balance
- `model_schema`: fetch parameter schema for a model
- `get_task_details`: check status and results for a previous task

## Integration with OpenClaw

When running inside an OpenClaw agent workflow, invoke the generator with:

```bash
python scripts/generate.py --prompt "cat portrait" --mode image
```

The script will:
1. Load credentials from `.env` or environment variables
2. Select default model parameters for the chosen modality
3. Execute the request and save output to disk

## Testing

Run unit tests:

```bash
pytest -q -m "not integration"
```

## Migration from v1.x

When updating from earlier REST-based scripts:

- Install the SDK: `pip install runware-sdk`
- Use `scripts/generate.py` in place of `scripts/generate_image.py`
- Existing CLI flags (`--prompt`, `--outfile`, `--size`, `--model`, `--num-results`, `--sync`) remain supported
- Use `--mode` to target video, audio, text, or 3D generation
- Use `scripts/runware_mcp.py` for direct tool-style queries
