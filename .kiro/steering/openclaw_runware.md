---
inclusion: always
---

# OpenClaw Runware Skill

Multi-modal Runware.ai skill for OpenClaw: image, video, audio, text, and 3D generation through the official `runware-sdk`, plus MCP-style tooling. Python 3.11+.

## Architecture

- `scripts/generate.py` — main CLI generator. Builds a task payload from `--mode` (`image`/`video`/`audio`/`text`/`3d`), sends it via the async `Runware` client, saves each result to disk.
- `scripts/runware_mcp.py` — MCP-style CLI exposing discrete tools (`run`, `list-models`, `model-pricing`, `model-details`, `account`) mirroring the hosted Runware MCP server's tool set.
- `skill-config.json` — non-secret defaults (`default_size`, `default_format`, `default_output_dir`); `last_output_dir` is auto-updated by `generate.py` after a save.
- `RUNWARE_API_KEY` comes from `.env` (see `.env_sample`) or the environment — never from `skill-config.json`.
- Both scripts open the SDK client per call as an async context manager: `async with Runware(api_key=..., transport="rest") as client:`. Don't hold a client open across multiple requests.
- This is v2: generation always goes through `runware-sdk`'s `Runware` client. Don't reintroduce raw `requests.post` calls to the old REST API or resurrect `generate_image.py`.

## Conventions

- Target Python 3.11+; use PEP 604 unions (`str | None`), not `Optional[str]`.
- Import the SDK lazily/defensively (`_import_runware()`), printing a `pip install runware-sdk` hint and `sys.exit(1)` on `ImportError` instead of letting it raise.
- Module-private helpers are prefixed with `_` (`_parse_size`, `_slugify`, `_resolve_outpath`, etc.) and are the pytest-covered unit surface — keep new helpers named and tested the same way.
- CLI parsing uses `argparse`. When a change applies to both entry points, update `generate.py` and `runware_mcp.py` together.
- Modes are driven by lookup tables (`SUPPORTED_MODES`, `MODES_TO_TASKTYPE`, `MODES_TO_EXT`, `_default_model()`). Adding a modality means extending all of them, per `CONTRIBUTING.md`.
- Catch `RunwareError` (has `.code`) before a generic `Exception` fallback; report failures to `stderr` and exit non-zero rather than letting a traceback surface to the CLI user.
- Settings precedence is CLI flag > `skill-config.json` value > hardcoded default — preserve this order when adding new configurable options.

## Safety & secrets

- Never log, print, or persist `RUNWARE_API_KEY` or any credential.
- `skill-config.json` is committed — keep it secret-free.
- Keep `_validate_prompt()`'s minor-safety check intact when touching prompt handling; it must hard-block (exit non-zero), not just warn, despite the "WARNING" text in its message.
- Don't remove `.env` from `.gitignore`; use placeholders (e.g. `your_key_here`) in examples and docs, never real keys.

## Testing & docs

- Unit tests live in `tests/test_generate.py`, one `Test*` class per function under test. Run with `pytest -q`.
- The integration test skips automatically without `RUNWARE_API_KEY` (`skipif`); CI (`.github/workflows/ci.yml`) runs Python 3.11–3.13 with `pytest -q -m "not integration"`.
- `README.md` and `SKILL.md` both carry CLI flag tables and quick-start snippets — update both when CLI behavior changes, and add matching usage examples to `examples/README.md`.
