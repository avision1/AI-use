"""Download a pinned, reproducible Kokoro edition; used at image build time."""
from .voices import PRESETS

MODEL_REPO = "hexgrad/Kokoro-82M"
MODEL_REVISION = "f3ff3571791e39611d31c381e3a41a3af07b4987"


def assets(voices=()):
    from huggingface_hub import hf_hub_download
    files = ["config.json", "kokoro-v1_0.pth", *[f"voices/{v}.pt" for v in voices]]
    return {f: hf_hub_download(repo_id=MODEL_REPO, filename=f, revision=MODEL_REVISION) for f in files}


if __name__ == "__main__":
    assets(PRESETS)
    print("Pinned Kokoro model and English voices cached.")
