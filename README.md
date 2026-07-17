# runware-mcp

[![GitHub Author](https://img.shields.io/badge/Author-GeekLord-181717?style=flat&logo=github)](https://github.com/GeekLord/)
[![Repository](https://img.shields.io/badge/Repository-OpenClaw__Runware__API-blue?style=flat&logo=github)](https://github.com/GeekLord/OpenClaw_Runware_API)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?style=flat&logo=python)](https://www.python.org/)

**Multi-modal Runware.ai skill** — image, video, audio, text, and 3D generation via the official `runware-sdk` Python library, plus MCP-style tooling.

This repository contains an OpenClaw-compatible skill that connects to [Runware.ai's MCP server](https://runware.ai/mcp) and exposes a clean Python CLI for generating media, browsing models, checking pricing, and managing your account.

## Features

- **Multi-modal** — Generate images, videos, audio, text, and 3D models
- **Official SDK** — Uses `runware-sdk` (async, typed, JSON-Schema validated)
- **MCP integration** — MCP-style tools (`run`, `list-models`, `model-pricing`, `model-details`, `account`)
- **Hosted MCP server** — Can connect directly to `https://mcp.runware.ai` (OAuth 2.1, no local install needed)
- **Sync + async** — Sync delivery for fast tasks, async polling for long-running ones
- **Safe-by-default** — Lightweight prompt filtering
- **Configurable** — Default model, size, format via `skill-config.json`
- **Tested** — Pytest unit tests + optional integration tests

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set your API key
echo "RUNWARE_API_KEY=your_key_here" > .env

# Generate an image
python scripts/generate.py --prompt "A serene mountain landscape" --mode image --outfile landscape.png

# Generate a video
python scripts/generate.py --prompt "Waves crashing on a beach" --mode video --duration 8 --outfile waves.mp4

# Browse models via MCP-style CLI
python scripts/runware_mcp.py list-models --category image --search "flux"

# Check account balance
python scripts/runware_mcp.py account
```

## MCP Server Connection

### 1. Hosted (easiest — no install)

Any MCP-compatible client can connect to Runware's hosted server:

```json
{
  "mcpServers": {
    "runware": { "url": "https://mcp.runware.ai" }
  }
}
```

Authentication is handled via OAuth 2.1 — your API key stays server-side, encrypted in the OAuth session.

### 2. Local (self-hosted)

```json
{
  "mcpServers": {
    "runware": {
      "command": "npx",
      "args": ["-y", "@runware/mcp"],
      "env": { "RUNWARE_API_KEY": "your-api-key" }
    }
  }
}
```

### 3. Python (this skill)

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

## Files

| File | Purpose |
|------|---------|
| `scripts/generate.py` | Main multi-modal generator |
| `scripts/runware_mcp.py` | MCP-style CLI tool interface |
| `skill-config.json` | Default settings (no secrets) |
| `SKILL.md` | OpenClaw skill metadata & usage |
| `tests/test_generate.py` | Pytest tests |
| `examples/` | Example commands |

## Configuration

`skill-config.json` fields:

- `default_size` — default image size (e.g. `"1024x1024"`)
- `default_format` — output format (`png`/`jpg`/`webp`/`mp4`/`wav`/`glb`)
- `default_output_dir` — default output directory
- `last_output_dir` — auto-updated by the script

## CLI Reference

### `scripts/generate.py`

| Flag | Description |
|------|-------------|
| `--prompt` | Text prompt |
| `--mode` | `image`, `video`, `audio`, `text`, or `3d` |
| `--model` | Runware model ID (e.g. `runware:400@1`) |
| `--size` | Dimensions (e.g. `1024x1024`) |
| `--sync` / `--no-sync` | Sync vs async delivery |
| `--duration` | Video duration (seconds) |
| `--num-results` | Number of outputs |
| `--extra KEY VALUE` | Extra payload parameters |
| `--outfile` | Output filename |

### `scripts/runware_mcp.py`

| Command | Description |
|---------|-------------|
| `run --prompt "..."` | Run inference task |
| `list-models` | Browse model catalog |
| `model-pricing --model X` | Get model pricing |
| `model-details --model X` | Get model metadata |
| `account` | Show account info & balance |

## Testing

```bash
pytest -q
```

Integration tests require `RUNWARE_API_KEY` set in the environment.

## Safety

- Prompt filter blocks requests referencing minors
- Users must follow [Runware's terms of service](https://runware.ai/terms)
- API key stays client-side or in OAuth session — never committed

## Architecture

```mermaid
graph TD
    User[User / Terminal] -->|Prompt| Gen[scripts/generate.py]
    User -->|Tool call| MCP[scripts/runware_mcp.py]
    Gen -->|async with Runware| SDK[runware-sdk]
    MCP -->|async with Runware| SDK
    SDK -->|"run()"| API[Runware.ai API]
    API -->|Results| SDK
    SDK -->|Decoded output| Gen
    SDK -->|Decoded output| MCP
    Gen -->|Save| Output[Local file]
    MCP -->|Print| Output2[JSON stdout]

    MCP_Client[MCP Client e.g. Claude Desktop]
    MCP_Client -->|stdio / HTTP| MCP_Server["npx @runware/mcp"]
    MCP_Server --> API
```

## Migration from v1.x

| Old | New |
|-----|-----|
| `scripts/generate_image.py` | `scripts/generate.py` |
| `requests.post` to `/v1/tasks` | `runware-sdk` `client.run()` |
| Manual UUIDs & response parsing | SDK handles schema, validation, delivery |
| Image-only | Image + video + audio + text + 3D |
| Python 3.8+ | Python 3.11+ |

## Author

**Shobhit Kumar Prabhakar** — [@GeekLord](https://github.com/GeekLord/)

## License

MIT — see LICENSE.

## Links

- [Runware MCP Server](https://runware.ai/mcp)
- [Runware MCP Docs](https://runware.ai/docs/platform/mcp)
- [Runware Python SDK](https://runware.ai/docs/platform/python)
- [Official @runware/mcp GitHub](https://github.com/runware/mcp)
