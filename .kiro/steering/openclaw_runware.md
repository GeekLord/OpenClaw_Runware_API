---
inclusion: always
---

# OpenClaw Runware skill

Multi-modal Runware.ai skill for OpenClaw: image, video, audio, text, and 3D generation through the official `runware-sdk` library and MCP tooling. Requires Python 3.11+.

## Architecture

- `scripts/generate.py`: Main CLI generator. Builds task payloads from `--mode` (`image`, `video`, `audio`, `text`, `3d`), submits requests via an asynchronous `Runware` client session, and saves outputs to disk.
- `scripts/runware_mcp.py`: MCP CLI exposing discrete tools (`run`, `list-models`, `model-pricing`, `model-details`, `account`) matching the hosted Runware MCP server tool catalog.
- `skill-config.json`: Non-sensitive configuration defaults (`default_size`, `default_format`, `default_output_dir`). The `last_output_dir` property is updated automatically by `generate.py` after writing an output file.
- `RUNWARE_API_KEY`: Sourced from `.env` (see `.env_sample`) or system environment variables. Never stored in `skill-config.json`.
- SDK sessions: Both scripts initialize `Runware` as an asynchronous context manager (`async with Runware(api_key=..., transport="rest") as client:`). Do not share or persist client connections across separate runs.
- Generation engine: Generation routes through `runware-sdk`. Avoid raw REST requests or legacy standalone image scripts.

## Conventions

- Python runtime: Python 3.11+. Use PEP 604 union syntax (`str | None`) rather than `Optional[str]`.
- Dependency checks: Import the SDK with `_import_runware()`, logging a `pip install runware-sdk` hint and exiting with code 1 when the package is missing.
- Private helpers: Prefix internal utilities with `_` (`_parse_size`, `_slugify`, `_resolve_outpath`, etc.) and maintain unit test coverage in `tests/`.
- CLI arguments: Use `argparse`. Keep flags and options consistent across `generate.py` and `runware_mcp.py`.
- Modality mapping: Modalities are defined in `SUPPORTED_MODES`, `MODES_TO_TASKTYPE`, `MODES_TO_EXT`, and `_default_model()`. Adding a modality requires updating all mappings and test cases.
- Error handling: Catch `RunwareError` before general `Exception` handlers. Write error details to `sys.stderr` and exit with a non-zero code.
- Configuration precedence: Command-line arguments override `skill-config.json` values, which override module defaults.

## Safety and secrets

- Do not log, print, or persist API credentials.
- Keep `skill-config.json` free of credentials.
- Retain prompt validation in `_validate_prompt()` to block requests referencing minors.
- Ensure `.env` is ignored by git. Use placeholder strings in example commands.

## Testing and documentation

- Unit tests reside in `tests/test_generate.py` and `tests/test_runware_mcp.py`. Run tests using `pytest -q -m "not integration"`.
- Live integration tests require `RUNWARE_API_KEY` and are marked with `integration`.
- Maintain CLI reference tables and quick start examples in both `README.md` and `SKILL.md` when command options change.
