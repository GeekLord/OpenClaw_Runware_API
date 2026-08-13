import asyncio
import json
import os
import sys
from pathlib import Path

import pytest

# Ensure the project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import generate as gen


@pytest.fixture
def cfg(tmp_path):
    """Provide a temporary config dictionary."""
    return {
        "default_size": "64x64",
        "default_format": "png",
        "default_output_dir": str(tmp_path),
    }


class TestParseSize:
    def test_normal(self):
        assert gen._parse_size("1024x768") == (1024, 768)

    def test_capital_x(self):
        assert gen._parse_size("800X600") == (800, 600)

    def test_asterisk(self):
        assert gen._parse_size("512*512") == (512, 512)

    def test_empty(self):
        assert gen._parse_size("") == (1024, 1024)

    def test_invalid(self):
        assert gen._parse_size("invalid") == (1024, 1024)


class TestSlugify:
    def test_basic(self):
        assert gen._slugify("Hello World!") == "hello_world"

    def test_truncation(self):
        long_str = "a" * 100
        assert len(gen._slugify(long_str)) <= 50

    def test_empty_string(self):
        assert gen._slugify("") == "media"

    def test_special_characters(self):
        assert gen._slugify("A & B @ C # D") == "a_b_c_d"


class TestValidatePrompt:
    def test_clean(self):
        gen._validate_prompt("A portrait of an adult at sunset")

    def test_blocked_word(self):
        with pytest.raises(SystemExit):
            gen._validate_prompt("A teenage girl in a park")


class TestResolveOutpath:
    def test_default_dir(self, cfg):
        p = gen._resolve_outpath(0, "png", None, cfg, prompt="mountains")
        assert str(cfg["default_output_dir"]) in str(p)
        assert "mountains" in p.name
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

    def test_audio(self):
        m = gen._default_model("audio")
        assert isinstance(m, str) and len(m) > 0

    def test_text(self):
        m = gen._default_model("text")
        assert isinstance(m, str) and len(m) > 0

    def test_3d(self):
        m = gen._default_model("3d")
        assert isinstance(m, str) and len(m) > 0

    def test_fallback(self):
        m = gen._default_model("unknown_mode")
        assert m == "runware:101@1"


class TestSaveResults:
    def test_save_base64_image(self, tmp_path, cfg):
        import base64
        fake_bytes = b"fake_png_data"
        b64 = base64.b64encode(fake_bytes).decode("utf-8")
        results = [{"imageBase64Data": b64}]
        outfile = str(tmp_path / "saved.png")
        gen._save_results(results, "png", outfile, cfg, prompt="test", config_path=None)
        saved_file = tmp_path / "saved.png"
        assert saved_file.exists()
        assert saved_file.read_bytes() == fake_bytes

    def test_save_text_content(self, tmp_path, cfg):
        results = [{"text": "Hello world from Runware"}]
        outfile = str(tmp_path / "poem.txt")
        gen._save_results(results, "txt", outfile, cfg, prompt="poem", config_path=None)
        saved_file = tmp_path / "poem.txt"
        assert saved_file.exists()
        assert saved_file.read_text(encoding="utf-8") == "Hello world from Runware"

    def test_save_json_fallback(self, tmp_path, cfg):
        results = [{"status": "queued", "id": "123"}]
        outfile = str(tmp_path / "result.json")
        gen._save_results(results, "json", outfile, cfg, prompt="status", config_path=None)
        saved_file = tmp_path / "result.json"
        assert saved_file.exists()
        data = json.loads(saved_file.read_text(encoding="utf-8"))
        assert data["id"] == "123"


@pytest.mark.integration
def test_integration_run_and_save(tmp_path):
    """Real API call: requires a valid RUNWARE_API_KEY."""
    api_key = os.getenv("RUNWARE_API_KEY")
    if not api_key or api_key in ("your_key_here", "YOUR_RUNWARE_KEY_HERE"):
        pytest.skip("Integration test requires a valid RUNWARE_API_KEY")

    try:
        from runware import Runware
    except ImportError:
        pytest.skip("runware-sdk not installed")

    try:
        results, ext = asyncio.run(
            gen.run_generation(
                mode="image",
                prompt="A small test image, photorealistic",
                model="runware:101@1",
                size="64x64",
                output_format="png",
                duration=None,
                num_results=1,
                sync=True,
            )
        )
    except Exception as e:
        pytest.skip(f"API call failed: {e}")

    assert len(results) > 0
    cfg = {
        "default_size": "64x64",
        "default_format": "png",
        "default_output_dir": str(tmp_path),
    }
    gen._save_results(
        results,
        ext,
        str(tmp_path / "test_out.png"),
        cfg,
        prompt="test",
        config_path=tmp_path / "config.json",
    )
    assert (tmp_path / "test_out.png").exists()
