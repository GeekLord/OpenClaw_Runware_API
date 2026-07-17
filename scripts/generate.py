#!/usr/bin/env python3
"""
Generate media via Runware.ai SDK — image, video, audio, text, 3D — and save results.

Usage:
  python scripts/generate.py --prompt "..." [--outfile NAME] [--size 1024x1024] [--model "runware:400@1"] [--mode image]
  python scripts/generate.py --prompt "..." --mode video --duration 8

Supports sync delivery for fast tasks (images) and async polling for long tasks (video).
Uses the official `runware-sdk` (Python 3.11+).

Requires RUNWARE_API_KEY env variable.
"""

import argparse
import asyncio
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(path): pass

HERE = Path(__file__).resolve().parent.parent
CONFIG_PATH = HERE / "skill-config.json"
ENV_PATH = HERE / ".env"

load_dotenv(ENV_PATH)

# ── Lazy SDK import with friendly error ──────────────────────────────────────

def _import_runware():
    try:
        from runware import Runware, RunwareError
        return Runware, RunwareError
    except ImportError:
        print("ERROR: runware-sdk not installed.", file=sys.stderr)
        print("Run: pip install runware-sdk", file=sys.stderr)
        sys.exit(1)


# ── Modes & helpers ──────────────────────────────────────────────────────────

SUPPORTED_MODES = frozenset({"image", "video", "audio", "text", "3d"})

MODES_TO_TASKTYPE = {
    "image": "imageInference",
    "video": "videoInference",
    "audio": "audioInference",
    "text": "textInference",
    "3d": "threeDInference",
}

MODES_TO_EXT = {
    "image": "png",
    "video": "mp4",
    "audio": "wav",
    "text": "txt",
    "3d": "glb",
}


async def run_generation(
    mode: str,
    prompt: str,
    model: str | None,
    size: str,
    output_format: str,
    duration: int | None,
    num_results: int,
    sync: bool,
    **extra_payload: str,
):
    Runware, RunwareError = _import_runware()

    api_key = os.getenv("RUNWARE_API_KEY")
    if not api_key:
        print("ERROR: RUNWARE_API_KEY not set in environment or .env file.", file=sys.stderr)
        sys.exit(1)

    task_type = MODES_TO_TASKTYPE.get(mode, "imageInference")
    width, height = _parse_size(size)

    payload: dict = {
        "taskType": task_type,
        "model": model or _default_model(mode),
        "positivePrompt": prompt,
        "width": width,
        "height": height,
        "deliveryMethod": "sync" if sync else "async",
        "numberResults": num_results,
    }

    # Mode-specific extras
    if mode == "video" and duration:
        payload["duration"] = duration
    if mode == "text":
        payload.pop("positivePrompt", None)
        payload.pop("width", None)
        payload.pop("height", None)
        payload["messages"] = [{"role": "user", "content": prompt}]

    # Merge extra payload keys (e.g. --extra "negativePrompt=blurry" --extra "CFGScale=7")
    for k, v in extra_payload.items():
        if v is not None:
            try:
                v = json.loads(v)
            except (json.JSONDecodeError, TypeError):
                pass
            payload[k] = v

    if mode != "text":
        _validate_prompt(prompt)

    ext = output_format or MODES_TO_EXT.get(mode, "png")
    print(f"[{mode}] Sending to Runware (model={payload['model']}, size={width}x{height}, sync={sync})...")

    async with Runware(api_key=api_key, transport="rest") as client:
        try:
            results = await client.run(payload)
        except RunwareError as e:
            print(f"Runware API error [{e.code}]: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            sys.exit(1)

    if not results:
        print("No results returned.", file=sys.stderr)
        sys.exit(1)

    return results, ext


def _default_model(mode: str) -> str:
    defaults = {
        "image": "runware:101@1",
        "video": "klingai:kling-video@3-4k",
        "audio": "inworld:tts-1.5-max@1",
        "text": "deepseek:deepseek-v4-chat@1",
        "3d": "runware:3d@1",
    }
    return defaults.get(mode, "runware:101@1")


def _parse_size(size: str) -> tuple[int, int]:
    if "x" in size:
        parts = size.split("x")
        return int(parts[0]), int(parts[1])
    return 1024, 1024


def _validate_prompt(prompt: str):
    ban_words = ["teen", "teenage", "minor", "13", "14", "15", "16", "17", "18", "19"]
    low = prompt.lower()
    for w in ban_words:
        if w in low:
            print(
                "WARNING: Prompt appears to reference a minor. Please confirm subject is 21+ and retry.",
                file=sys.stderr,
            )
            sys.exit(1)


def _slugify(s: str, max_len: int = 50) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    if len(s) > max_len:
        s = s[:max_len].rstrip("_")
    return s or "media"


def _save_results(results: list[dict], ext: str, outfile: str | None, cfg: dict):
    """Save each result (image, video URL, text content, etc.) to disk."""
    saved_paths = []

    for idx, item in enumerate(results):
        # Determine output path
        out = _resolve_outpath(idx, ext, outfile, cfg)
        suffix = "" if len(results) == 1 else f"_{idx}"
        if suffix and outfile and not outfile.endswith(suffix + "."):
            stem = out.stem + suffix
            out = out.with_stem(stem)

        # Save based on what's available
        image_b64 = item.get("imageBase64Data") or item.get("imageBase64")
        image_url = item.get("imageURL")
        video_url = item.get("videoURL") or item.get("mediaURL")
        audio_url = item.get("audioURL") or item.get("mediaURL")
        model_url = item.get("threeDURL") or item.get("mediaURL")
        text_content = item.get("text") or item.get("content")

        if image_b64:
            import base64 as b64mod
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(b64mod.b64decode(image_b64))
            saved_paths.append(out)
            print(f"[{idx}] Saved image: {out}")

        elif image_url or video_url or audio_url or model_url:
            url = image_url or video_url or audio_url or model_url
            out.parent.mkdir(parents=True, exist_ok=True)
            _download_file(url, out)
            saved_paths.append(out)
            print(f"[{idx}] Saved media: {out} (from {url})")

        elif text_content:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(text_content, encoding="utf-8")
            saved_paths.append(out)
            print(f"[{idx}] Saved text: {out}")

        else:
            # Fallback: dump raw JSON metadata
            out = out.with_suffix(".json")
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(item, indent=2, default=str), encoding="utf-8")
            saved_paths.append(out)
            print(f"[{idx}] Saved metadata: {out}")

    # Remember last used directory
    if saved_paths:
        try:
            cfg["last_output_dir"] = str(saved_paths[0].parent)
            CONFIG_PATH.write_text(json.dumps(cfg, indent=2))
        except Exception:
            pass


def _resolve_outpath(idx: int, ext: str, outfile: str | None, cfg: dict) -> Path:
    default_dir = cfg.get("default_output_dir", "~/runware_output")
    last_dir = cfg.get("last_output_dir")

    if outfile:
        expanded = os.path.expandvars(os.path.expanduser(outfile))
        out = Path(expanded)
        if not out.is_absolute():
            base = Path(last_dir) if last_dir else Path(default_dir).expanduser()
            base.mkdir(parents=True, exist_ok=True)
            out = base / out
        else:
            out.parent.mkdir(parents=True, exist_ok=True)
        return out

    out_dir = Path(last_dir).expanduser() if last_dir else Path(default_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = _slugify("")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return out_dir / f"{slug}_{ts}_{idx}.{ext}"


def _download_file(url: str, dest: Path):
    import urllib.request
    try:
        urllib.request.urlretrieve(url, dest)
    except Exception as e:
        print(f"  WARNING: failed to download {url}: {e}", file=sys.stderr)


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="Runware.ai SDK generator — multi-modal (image / video / audio / text / 3D)",
    )
    ap.add_argument("--prompt", help="Text prompt for generation")
    ap.add_argument("--mode", choices=sorted(SUPPORTED_MODES), default="image",
                    help="Generation mode (default: image)")
    ap.add_argument("--outfile", default=None,
                    help="Output filename (relative → default dir, absolute → that path)")
    ap.add_argument("--size", default=None,
                    help="Image/video dimensions e.g. 1024x1024 (default from config)")
    ap.add_argument("--model", default=None,
                    help="Runware model identifier e.g. runware:400@1, klingai:kling-video@3-4k")
    ap.add_argument("--sync", action="store_true", default=True,
                    help="Use sync delivery (default)")
    ap.add_argument("--no-sync", action="store_false", dest="sync",
                    help="Use async delivery (polling)")
    ap.add_argument("--num-results", type=int, default=1,
                    help="Number of results to generate (default: 1)")
    ap.add_argument("--duration", type=int, default=None,
                    help="Video duration in seconds (video mode only)")
    ap.add_argument("--format", dest="output_format", default=None,
                    help="Output format override (png, jpg, mp4, wav, etc.)")
    ap.add_argument("--extra", action="append", nargs=2, metavar=("KEY", "VALUE"),
                    default=[], help="Extra payload key-value pairs (repeatable)")

    args = ap.parse_args()

    prompt = args.prompt
    if not prompt and args.mode != "text":
        print("ERROR: --prompt is required for this mode.", file=sys.stderr)
        sys.exit(1)

    cfg = json.loads(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}
    size = args.size or cfg.get("default_size", "1024x1024")
    out_format = args.output_format or cfg.get("default_format", "png")

    extra = dict(args.extra)

    results, ext = asyncio.run(
        run_generation(
            mode=args.mode,
            prompt=prompt or "",
            model=args.model,
            size=size,
            output_format=out_format,
            duration=args.duration,
            num_results=args.num_results,
            sync=args.sync,
            **extra,
        )
    )

    _save_results(results, ext, args.outfile, cfg)

    # Report metadata
    print(f"\nDone! Generated {len(results)} result(s).")


if __name__ == "__main__":
    main()
