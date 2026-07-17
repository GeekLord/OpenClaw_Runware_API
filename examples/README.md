# Example Commands

## Images

```bash
# Basic image generation (sync)
python scripts/generate.py --prompt "A photorealistic portrait of an adult in studio lighting" --mode image --outfile portrait.png

# With a specific model
python scripts/generate.py --prompt "Cyberpunk street scene, neon lights, rain" --model "runware:400@1" --size 1536x1024 --outfile cyberpunk.png

# Multiple results
python scripts/generate.py --prompt "Abstract geometric art" --num-results 4 --outfile abstract.png
```

## Videos

```bash
# Short video clip
python scripts/generate.py --prompt "Waves crashing on a tropical beach at sunset" --mode video --duration 8 --outfile beach.mp4

# Use a specific video model
python scripts/generate.py --prompt "Cinematic drone shot over mountains" --mode video --model "google:veo-3.1@1" --duration 10 --outfile mountains.mp4
```

## Audio

```bash
# Text-to-speech
python scripts/generate.py --prompt "Welcome to the future of AI generation" --mode audio --model "inworld:tts-1.5-max@1" --outfile welcome.wav
```

## Text

```bash
# LLM inference
python scripts/generate.py --prompt "Write a short poem about artificial intelligence" --mode text --outfile poem.txt
```

## 3D

```bash
# 3D model generation
python scripts/generate.py --prompt "A low-poly chair" --mode 3d --outfile chair.glb
```

## MCP-style CLI

```bash
# Browse image models
python scripts/runware_mcp.py list-models --category image --search "flux"

# Get pricing
python scripts/runware_mcp.py model-pricing --model "runware:101@1"

# Check account balance
python scripts/runware_mcp.py account

# Run via MCP tool
python scripts/runware_mcp.py run --prompt "A cat in a forest" --mode image
```

## Async mode (polling)

```bash
# Long task with async delivery
python scripts/generate.py --prompt "Cinematic spaceship launch" --mode video --no-sync --duration 12 --outfile launch.mp4
```
