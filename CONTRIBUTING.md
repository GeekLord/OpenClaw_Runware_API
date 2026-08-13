# Contributing to runware-mcp

Thank you for helping improve this project.

## Getting started

1. Fork the repository and open a pull request against `main`.
2. Install development packages: `pip install -r requirements.txt`
3. Run the test suite: `pytest -q -m "not integration"`
4. To run live integration tests, set `RUNWARE_API_KEY` in your environment.

## Guidelines

- Keep pull requests focused on a single change or feature.
- Include unit tests for bug fixes or new functionality.
- Update `SKILL.md`, `README.md`, and `examples/README.md` when changing CLI arguments or default settings.
- Write clear commit messages.
- Keep external dependencies minimal.

## Adding a new mode

When adding a new generation modality:

1. Update `SUPPORTED_MODES`, `MODES_TO_TASKTYPE`, `MODES_TO_EXT`, and `_default_model()` in `scripts/generate.py`.
2. Update the `--mode` choices in `scripts/runware_mcp.py`.
3. Add corresponding tests in `tests/test_generate.py` and `tests/test_runware_mcp.py`.
4. Add example commands in `examples/README.md`.

## Reporting issues

Open an issue for bugs, documentation errors, or feature suggestions. Please include steps to reproduce unexpected behavior and sample inputs when possible.
