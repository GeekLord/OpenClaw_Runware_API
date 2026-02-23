import subprocess
import shlex

prompt = (
    "hyper-realistic portrait of a young North Indian woman with light skin, intense dark eyes, and dark hair pulled back, "
    "wearing a vibrant red and orange traditional blouse with intricate patterns, yellow salwar, and flowing dupatta. "
    "Add ornate jhumka earrings and a small pendant necklace. Use warm colors, shallow depth of field, and high resolution (300 DPI) "
    "to capture textures and details. Emphasize her presence and evoke warmth and celebration."
)

script = r"C:\Users\Shobhit\.openclaw\workspace\skills\runware-image\scripts\generate_image.py"
for i in range(1,6):
    outfile = rf"C:\Users\Shobhit\Downloads\north_indian_portrait_default_p{i}.png"
    cmd = ["python", script, "--prompt", prompt, "--sync", "--size", "1024x1536", "--outfile", outfile]
    print("Running:", " ".join(shlex.quote(c) for c in cmd))
    try:
        subprocess.check_call(cmd, timeout=180)
    except subprocess.CalledProcessError as e:
        print("Command failed:", e)
        break
    except subprocess.TimeoutExpired:
        print("Command timed out")
        break
