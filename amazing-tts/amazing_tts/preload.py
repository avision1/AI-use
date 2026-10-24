"""Download a pinned, reproducible Kokoro edition; used at image build time."""
from .voices import PRESETS
from functools import lru_cache

MODEL_REPO = "hexgrad/Kokoro-82M"
MODEL_REVISION = "f3ff3571791e39611d31c381e3a41a3af07b4987"


@lru_cache(maxsize=64)
def asset(filename):
    from huggingface_hub import hf_hub_download
    from huggingface_hub.errors import LocalEntryNotFoundError
    try:
        # Revisions are pinned: a cached file never needs a network freshness check.
        return hf_hub_download(repo_id=MODEL_REPO, filename=filename, revision=MODEL_REVISION, local_files_only=True)
    except LocalEntryNotFoundError:
        return hf_hub_download(repo_id=MODEL_REPO, filename=filename, revision=MODEL_REVISION)


def assets(voices=()):
    files = ["config.json", "kokoro-v1_0.pth", *[f"voices/{v}.pt" for v in voices]]
    return {filename: asset(filename) for filename in files}


if __name__ == "__main__":
    assets(PRESETS)
    print("Pinned Kokoro model and English voices cached.")
