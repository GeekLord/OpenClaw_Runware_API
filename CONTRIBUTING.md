# Contributing to runware-mcp

Thank you for your interest in improving this skill!

## Getting Started

1. Fork the repository and submit a pull request against `main`.
2. Install development dependencies: `pip install -r requirements.txt`
3. Run tests: `pytest -q`
4. For integration tests, set `RUNWARE_API_KEY` in your environment.

## Guidelines

- **Keep changes focused** — open separate PRs for separate features
- **Include tests** — add unit tests for new behaviors, update existing tests when behavior changes
- **Update docs** — if you add a feature, update `SKILL.md`, `README.md`, and examples as appropriate
- **Use clear commit messages** — reference issue numbers where applicable
- **Minimal dependencies** — avoid adding new packages unless necessary

## Adding a New Mode

To add a new generation mode (e.g., a new modality):

1. Add the mode to `SUPPORTED_MODES`, `MODES_TO_TASKTYPE`, `MODES_TO_EXT`, and `_default_model()` in `scripts/generate.py`
2. Add the corresponding `--mode` choice in `scripts/runware_mcp.py`
3. Update tests accordingly
4. Add example commands to `examples/README.md`

## Reporting Issues

Open issues for bugs, feature requests, or documentation corrections. Include steps to reproduce and minimal examples when possible.
