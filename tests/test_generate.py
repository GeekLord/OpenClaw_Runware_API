import asyncio
import json
from pathlib import Path
import os
import sys

import pytest

# Ensure the scripts dir is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import generate as gen


@pytest.fixture
def cfg(tmp_path):
    """Provide a temp config dictionary."""
    return {
        "default_size": "64x64",
        "default_format": "png",
        "default_output_dir": str(tmp_path),
    }


class TestParseSize:
    def test_normal(self):
        assert gen._parse_size("1024x768") == (1024, 768)

    def test_fallback(self):
        assert gen._parse_size("") == (1024, 1024)


class TestSlugify:
    def test_basic(self):
        assert gen._slugify("Hello World!") == "hello_world"

    def test_truncation(self):
        long_str = "a" * 100
        assert len(gen._slugify(long_str)) <= 50


class TestValidatePrompt:
    def test_clean(self):
        gen._validate_prompt("A portrait of an adult at sunset")  # no raise

    def test_blocked_word(self):
        with pytest.raises(SystemExit):
            gen._validate_prompt("A teenage girl in a park")


class TestResolveOutpath:
    def test_default_dir(self, cfg):
        p = gen._resolve_outpath(0, "png", None, cfg)
        assert str(cfg["default_output_dir"]) in str(p)
        assert p.suffix == ".png"

    def test_absolute_outfile(self, tmp_path, cfg):
        target = tmp_path / "custom.png"
        p = gen._resolve_outpath(0, "png", str(target), cfg)
        assert p == target

    def test_relative_outfile(self, cfg):
        p = gen._resolve_outpath(0, "png", "result.png", cfg)
        assert p.name == "result.png"
        assert p.suffix == ".png"


class TestDefaultModel:
    def test_image(self):
        m = gen._default_model("image")
        assert isinstance(m, str) and len(m) > 0

    def test_video(self):
        m = gen._default_model("video")
        assert isinstance(m, str) and len(m) > 0


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.getenv("RUNWARE_API_KEY") is None,
    reason="Integration test requires RUNWARE_API_KEY",
)
async def test_integration_run_and_save(tmp_path):
    """Real API call — requires a valid key."""
    # Save a result to verify the pipeline works end-to-end
    results, ext = await gen.run_generation(
        mode="image",
        prompt="A small test image, photorealistic",
        model="runware:101@1",
        size="64x64",
        output_format="png",
        duration=None,
        num_results=1,
        sync=True,
    )
    assert len(results) > 0
    cfg = {
        "default_size": "64x64",
        "default_format": "png",
        "default_output_dir": str(tmp_path),
    }
    gen._save_results(results, ext, str(tmp_path / "test_out.png"), cfg)
    assert (tmp_path / "test_out.png").exists()
