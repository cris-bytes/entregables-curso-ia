"""Descarga pesos públicos a una caché local ignorada por Git."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("HF_HOME", str(ROOT / ".cache" / "huggingface"))
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
from huggingface_hub import HfApi, snapshot_download

def main():
    lock_path = ROOT / "models.lock.json"
    if lock_path.exists():
        models = json.loads(lock_path.read_text())
    else:
        names = {"embedding": "intfloat/multilingual-e5-small", "generator": "Qwen/Qwen2.5-1.5B-Instruct",
                 "generator_small": "Qwen/Qwen2.5-0.5B-Instruct"}
        models = {key: {"repo": repo, "revision": HfApi().model_info(repo).sha} for key, repo in names.items()}
        lock_path.write_text(json.dumps(models, indent=2) + "\n")
    for key, model in models.items():
        print(f"Descargando {key}: {model['repo']} @ {model['revision']}", flush=True)
        snapshot_download(model["repo"], revision=model["revision"],
                          cache_dir=str(ROOT / ".cache" / "huggingface" / "hub"),
                          allow_patterns=["*.json", "*.safetensors", "*.txt", "*.model", "*.py", "*.md"],
                          ignore_patterns=["onnx/*", "openvino/*"], max_workers=4)
    print("Modelos descargados. La inferencia posterior puede funcionar sin internet.")

if __name__ == "__main__":
    main()
