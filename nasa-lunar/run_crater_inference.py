#!/usr/bin/env python3
"""Bounded local NAC crater-inference evidence for the NASA--IBM release.

This is a demonstration harness, not an mAP replication.  It reuses the
pinned notebook's preprocessing, checkpoint loading, and score floor while
recording every raw detector output used in the rendered panels.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import platform
import resource
import sys
import time
from pathlib import Path

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import torch
import torchvision
import lightning
import terratorch
import timm
import torchmetrics

import terratorch_integration  # registers NASA--IBM backbone/task
from terratorch_integration import LunarObjectDetectionTask


ROOT = Path(__file__).resolve().parent
CODE = ROOT / "NASA-IBM-Lunar-Foundation-Model"
OUT = ROOT / "outputs"
CKPT = ROOT / "inputs/model/crater/NAC_ni_lfm_ps8_s44.ckpt"
BACKBONE_CFG = ROOT / "inputs/model/base/backbone/config.yaml"
ANN = ROOT / "inputs/dataset/annotations_min5px_test.json"
SCORE_FLOOR = 0.05
THRESHOLDS = (0.3, 0.5, 0.7)
NORM_MEAN, NORM_STD = 0.346548, 0.159291
TARGET_BOX = [127.2, 122.5, 147.5, 140.0]  # supplied by the official notebook
TEST_TILES = [
    "images/NAC_DTM_A15SIVB_PHO_E009S3481__large_box1__r0_c0.npy",
    "images/NAC_DTM_HLNDPHOTOM2_PHO_E011N1499__standard_box3__r0_c0.npy",
    "images/NAC_DTM_HLNDPHOTOM2_PHO_E011N1499__standard_box3__r0_c225.npy",
    "images/NAC_DTM_HLNDPHOTOM2_PHO_E011N1499__standard_box3__r0_c451.npy",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def mem_available_bytes() -> int | None:
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) * 1024
    return None


def package_version(module) -> str:
    return str(getattr(module, "__version__", "unknown"))


def xyxy_from_coco(box):
    x, y, w, h = box
    return [float(x), float(y), float(x + w), float(y + h)]


def draw_boxes(ax, boxes, color, linewidth=1.0):
    for box in boxes:
        x1, y1, x2, y2 = box
        ax.add_patch(patches.Rectangle((x1, y1), x2 - x1, y2 - y1,
                                       linewidth=linewidth, edgecolor=color,
                                       facecolor="none"))


def render_impact(images, records):
    fig, axes = plt.subplots(2, 2, figsize=(10, 10))
    for col, name in enumerate(("pre_256_native", "post_256_native")):
        rec = records[name]
        for row in range(2):
            ax = axes[row, col]
            ax.imshow(images[name], cmap="gray", vmin=0, vmax=255)
            ax.axis("off")
            if row == 1:
                draw_boxes(ax, [d["box_xyxy"] for d in rec["detections"] if d["score"] >= 0.5], "#00BFFF", 0.9)
            if name == "post_256_native":
                draw_boxes(ax, [TARGET_BOX], "#FF8C00", 1.8)
            ax.set_title(("Post-impact" if name.startswith("post") else "Pre-impact") +
                         ("; detector boxes (blue)" if row else ""))
    fig.suptitle("Official SpaceX pair. Orange = supplied notebook target, not a detection.")
    fig.tight_layout()
    fig.savefig(OUT / "impact_comparison.png", dpi=180)
    plt.close(fig)


def render_tile(rec):
    image = np.load(ROOT / rec["path"]).astype(np.uint8)
    fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    axes[0].imshow(image, cmap="gray", vmin=0, vmax=255)
    axes[0].set_title("Dataset ground truth (green)")
    draw_boxes(axes[0], rec["annotation"]["boxes_xyxy"], "#00FF7F")
    axes[1].imshow(image, cmap="gray", vmin=0, vmax=255)
    axes[1].set_title("NI-LFM predictions at score >= 0.5 (blue)")
    draw_boxes(axes[1], [d["box_xyxy"] for d in rec["detections"] if d["score"] >= 0.5], "#00BFFF")
    for ax in axes:
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(OUT / (Path(rec["id"]).stem + "_gt_vs_prediction.png"), dpi=180)
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(2)
    torch.manual_seed(0)
    np.random.seed(0)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device != "cuda":
        raise RuntimeError("This bounded run was authorized for CUDA but CUDA is unavailable.")

    before_mem = mem_available_bytes()
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    load_start = time.perf_counter()
    checkpoint = torch.load(CKPT, map_location="cpu", weights_only=False)
    model_args = copy.deepcopy(checkpoint["hyper_parameters"]["model_args"])
    del checkpoint
    model_args["backbone_cfg"] = str(BACKBONE_CFG)
    model_args["backbone_checkpoint_path"] = None
    model = LunarObjectDetectionTask.load_from_checkpoint(
        CKPT, map_location="cpu", model_args=model_args,
    ).eval().to(device)
    torch.cuda.synchronize()
    model_load_seconds = time.perf_counter() - load_start

    def detect(array: np.ndarray):
        normalized = (array.astype(np.float32) / 255.0 - NORM_MEAN) / NORM_STD
        tensor = torch.tensor(normalized).unsqueeze(0).unsqueeze(0).to(device)
        start = time.perf_counter()
        with torch.inference_mode():
            pred = model.model(tensor).output[0]
        torch.cuda.synchronize()
        seconds = time.perf_counter() - start
        detections = []
        for box, score, label in zip(pred["boxes"].cpu().numpy().tolist(),
                                     pred["scores"].cpu().numpy().tolist(),
                                     pred["labels"].cpu().numpy().tolist()):
            if score >= SCORE_FLOOR:
                detections.append({"box_xyxy": [float(x) for x in box],
                                   "score": float(score), "label": int(label)})
        return detections, seconds

    images = {
        "pre_256_native": np.asarray(Image.open(CODE / "examples/spacex_crater/pre_256_native.png").convert("L"), dtype=np.uint8),
        "post_256_native": np.asarray(Image.open(CODE / "examples/spacex_crater/post_256_native.png").convert("L"), dtype=np.uint8),
    }
    records = {}
    for name, image in images.items():
        detections, seconds = detect(image)
        path = CODE / "examples/spacex_crater" / (name + ".png")
        records[name] = {
            "id": name, "kind": "official_pre_post_png", "path": str(path.relative_to(ROOT)),
            "sha256": sha256(path), "shape": list(image.shape), "inference_seconds": seconds,
            "annotation": {"kind": "hand_supplied_target" if name.startswith("post") else "none",
                           "boxes_xyxy": [TARGET_BOX] if name.startswith("post") else []},
            "detections": detections,
            "threshold_counts": {str(t): sum(d["score"] >= t for d in detections) for t in THRESHOLDS},
        }

    annotations = json.loads(ANN.read_text())
    image_ids = {entry["file_name"]: entry["id"] for entry in annotations["images"]}
    annotation_by_id = {}
    for annotation in annotations["annotations"]:
        annotation_by_id.setdefault(annotation["image_id"], []).append(xyxy_from_coco(annotation["bbox"]))
    test_records = []
    for rel in TEST_TILES:
        path = ROOT / "inputs/dataset" / rel
        tile = np.load(path).astype(np.uint8)
        detections, seconds = detect(tile)
        rec = {
            "id": rel, "kind": "official_test_split_tile", "path": str(path.relative_to(ROOT)),
            "sha256": sha256(path), "shape": list(tile.shape), "inference_seconds": seconds,
            "annotation": {"kind": "dataset_ground_truth", "boxes_xyxy": annotation_by_id.get(image_ids[rel], [])},
            "detections": detections,
            "threshold_counts": {str(t): sum(d["score"] >= t for d in detections) for t in THRESHOLDS},
        }
        test_records.append(rec)
        render_tile(rec)
    render_impact(images, records)

    after_mem = mem_available_bytes()
    raw = {
        "purpose": "bounded local inference evidence; not a paper-benchmark replication",
        "run": {
            "repo_commit": "d54c67aad513cb9daca444afa425cfb278e4fbf8",
            "script_sha256": sha256(Path(__file__)),
            "checkpoint": {"path": str(CKPT.relative_to(ROOT)), "sha256": sha256(CKPT), "size_bytes": CKPT.stat().st_size},
            "backbone_config": {"path": str(BACKBONE_CFG.relative_to(ROOT)), "sha256": sha256(BACKBONE_CFG), "size_bytes": BACKBONE_CFG.stat().st_size},
            "dataset_annotation": {"path": str(ANN.relative_to(ROOT)), "sha256": sha256(ANN), "size_bytes": ANN.stat().st_size},
            "device": torch.cuda.get_device_name(0), "backend": "CUDA", "cuda_version": torch.version.cuda,
            "versions": {"python": sys.version, "torch": torch.__version__, "torchvision": torchvision.__version__,
                         "lightning": package_version(lightning), "terratorch": package_version(terratorch),
                         "timm": package_version(timm), "torchmetrics": package_version(torchmetrics)},
            "compatibility_note": "Official requirements specify torch>=2.12 and torchvision>=0.27. This isolated qualification used inherited read-only torch 2.11.0+cu130 and isolated torchvision 0.26.0+cu130; success is not an official dependency reproduction.",
            "model_load_seconds": model_load_seconds,
            "cuda_peak_allocated_bytes": int(torch.cuda.max_memory_allocated()),
            "cuda_peak_reserved_bytes": int(torch.cuda.max_memory_reserved()),
            "host_mem_available_bytes_before": before_mem,
            "host_mem_available_bytes_after": after_mem,
            "process_max_rss_bytes": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024,
            "cpu_threads": 2,
        },
        "official_pre_post": list(records.values()),
        "test_split_tiles": test_records,
        "limits": [
            "Blue boxes are detector outputs after the stated score threshold.",
            "Orange post-impact box is a manually supplied official-notebook target annotation, not a detector prediction.",
            "Threshold counts are visualization diagnostics, not independent benchmarks.",
            "No precision, recall, or mAP is reported because this small local selection does not declare matching IoU and annotation rules.",
        ],
    }
    (OUT / "raw_results.json").write_text(json.dumps(raw, indent=2) + "\n")
    print(json.dumps({"raw_results": str(OUT / "raw_results.json"), "model_load_seconds": model_load_seconds,
                      "cuda_peak_allocated_bytes": raw["run"]["cuda_peak_allocated_bytes"]}, indent=2))


if __name__ == "__main__":
    main()
