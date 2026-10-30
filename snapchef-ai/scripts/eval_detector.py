"""Evaluate the pretrained SSDLite320 detector on COCO val2017 (held-out).

Thresholds are selected on a calibration split; the test split is reported
separately and is never used for threshold selection. Output:
  eval/detector_eval.json  (calibration thresholds + test metrics)
Run after downloading COCO val2017 + annotations into data/raw/coco/.
"""

import argparse
import io
import json
import math
import random
import zipfile
from pathlib import Path

from PIL import Image

from snapchef_ai.detector import IngredientDetector
from snapchef_ai.taxonomy import load_taxonomy

BASE_DIR = Path(__file__).resolve().parents[1]
COCO_DIR = BASE_DIR / "data" / "raw" / "coco"
IMAGES_ZIP = COCO_DIR / "val2017.zip"
ANNOTATIONS = COCO_DIR / "annotations" / "instances_val2017.json"
OUT_PATH = BASE_DIR / "eval" / "detector_eval.json"

TARGETS = ["apple", "banana", "orange", "broccoli", "carrot"]
PER_CLASS = 50
CALIBRATION_FRACTION = 0.4
SEED = 42
IOU_THRESHOLD = 0.3


def iou(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    union = area_a + area_b - inter
    return inter / union if union else 0.0


def normalize_box(box, width, height):
    return [box[0] / width, box[1] / height, box[2] / width, box[3] / height]


def collect_candidates(annotation_path, targets):
    payload = json.loads(annotation_path.read_text(encoding="utf-8"))
    categories = {
        category["id"]: category["name"] for category in payload["categories"]
    }
    name_to_id = {
        category["name"]: category["id"] for category in payload["categories"]
    }
    target_ids = {name_to_id[name] for name in targets if name in name_to_id}
    images = {image["id"]: image for image in payload["images"]}
    by_image = {image_id: [] for image_id in images}
    for annotation in payload["annotations"]:
        if annotation["category_id"] in target_ids and annotation["iscrowd"] == 0:
            image_id = annotation["image_id"]
            if image_id in by_image:
                by_image[image_id].append(annotation)
    candidates = {}
    for name in targets:
        candidates[name] = sorted(
            image_id
            for image_id, annotations in by_image.items()
            if any(
                categories[annotation["category_id"]] == name
                for annotation in annotations
            )
        )
    return payload, images, by_image, categories, candidates, target_ids


def prepare_records(
    records, images, by_image, target_category_ids, detector, images_zip
):
    """Run the detector once per record and cache detections + ground truth."""
    prepared = []
    for record in records:
        image_id = record["image_id"]
        target = record["target"]
        image_info = images[image_id]
        with images_zip.open(f"val2017/{image_info['file_name']}") as handle:
            image = Image.open(io.BytesIO(handle.read())).convert("RGB")
        width, height = image.size
        ground_truth = []
        for annotation in by_image[image_id]:
            if annotation["category_id"] not in target_category_ids[target]:
                continue
            ground_truth.append(normalize_box(annotation["bbox"], width, height))
        detections = [
            detection
            for detection in detector.detect(image)
            if detection.label == target
        ]
        prepared.append(
            {
                "image_id": image_id,
                "target": target,
                "ground_truth": ground_truth,
                "detections": detections,
            }
        )
    return prepared


def match_detections(detections, ground_truth, threshold):
    kept = [
        detection for detection in detections if detection.detection_score >= threshold
    ]
    kept_sorted = sorted(kept, key=lambda item: -item.detection_score)
    matched_gt = set()
    tp = 0
    for detection in kept_sorted:
        best_index = -1
        best_iou = IOU_THRESHOLD
        for index, box in enumerate(ground_truth):
            if index in matched_gt:
                continue
            value = iou(detection.box, box)
            if value >= best_iou:
                best_iou = value
                best_index = index
        if best_index >= 0:
            matched_gt.add(best_index)
            tp += 1
    fp = len(kept) - tp
    return tp, fp, len(matched_gt), len(ground_truth), len(kept)


def evaluate_prepared(prepared, threshold):
    total_tp = 0
    total_fp = 0
    total_gt = 0
    detected_images = 0
    fp_per_image = []
    scores_tp = []
    scores_fp = []
    multi_both_found = 0
    multi_total = 0
    count_errors = []

    for item in prepared:
        tp, fp, matched, gt_count, kept_count = match_detections(
            item["detections"], item["ground_truth"], threshold
        )
        total_tp += tp
        total_fp += fp
        total_gt += gt_count
        fp_per_image.append(fp)
        if tp >= 1:
            detected_images += 1
        for detection in item["detections"]:
            if detection.detection_score >= threshold:
                if detection in item["detections"][:0]:
                    pass
        for detection in sorted(
            [d for d in item["detections"] if d.detection_score >= threshold],
            key=lambda d: -d.detection_score,
        ):
            pass
        # Recompute score lists consistently with greedy matching.
        scores_tp.extend(
            [
                detection.detection_score
                for detection in sorted(
                    [d for d in item["detections"] if d.detection_score >= threshold],
                    key=lambda d: -d.detection_score,
                )
            ][:tp]
        )
        scores_fp.extend(
            [
                detection.detection_score
                for detection in sorted(
                    [d for d in item["detections"] if d.detection_score >= threshold],
                    key=lambda d: -d.detection_score,
                )
            ][tp:]
        )
        if gt_count >= 2:
            multi_total += 1
            if matched == gt_count:
                multi_both_found += 1
            count_errors.append(abs(kept_count - gt_count))

    precision = total_tp / max(total_tp + total_fp, 1)
    recall = total_tp / max(total_gt, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-9)
    detection_rate = detected_images / max(len(prepared), 1)
    mean_fp = sum(fp_per_image) / max(len(fp_per_image), 1)
    ece = compute_ece(scores_tp, scores_fp)
    return {
        "images": len(prepared),
        "ground_truth_boxes": total_gt,
        "true_positives": total_tp,
        "false_positives": total_fp,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "detection_rate": round(detection_rate, 4),
        "fp_per_image": round(mean_fp, 4),
        "ece": round(ece, 4),
        "multi_object": {
            "images": multi_total,
            "both_found_rate": round(multi_both_found / max(multi_total, 1), 4),
            "mean_count_error": round(sum(count_errors) / max(len(count_errors), 1), 4)
            if count_errors
            else 0.0,
        },
    }


def compute_ece(scores_tp, scores_fp):
    bins = [[] for _ in range(10)]
    for score in scores_tp:
        bins[min(9, int(score * 10))].append((score, 1))
    for score in scores_fp:
        bins[min(9, int(score * 10))].append((score, 0))
    total = len(scores_tp) + len(scores_fp)
    if total == 0:
        return 0.0
    ece = 0.0
    for bin_items in bins:
        if not bin_items:
            continue
        confidences = [item[0] for item in bin_items]
        accuracies = [item[1] for item in bin_items]
        ece += (len(bin_items) / total) * abs(
            sum(confidences) / len(confidences) - sum(accuracies) / len(accuracies)
        )
    return ece


def select_thresholds(prepared_by_target, targets):
    thresholds = {}
    for target in targets:
        prepared = prepared_by_target[target]
        candidate_scores = {0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9}
        for item in prepared:
            for detection in item["detections"]:
                candidate_scores.add(round(detection.detection_score, 4))
        best = None
        for threshold in sorted(candidate_scores):
            metrics = evaluate_prepared(prepared, threshold)
            key = (metrics["f1"], threshold)
            if best is None or key > best[0]:
                best = (key, threshold, metrics)
        thresholds[target] = best[1]
        print(
            f"{target}: threshold={best[1]:.3f} "
            f"f1={best[2]['f1']:.3f} precision={best[2]['precision']:.3f} "
            f"recall={best[2]['recall']:.3f} detection_rate={best[2]['detection_rate']:.3f} "
            f"fp_per_image={best[2]['fp_per_image']:.3f}"
        )
    return thresholds


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-class", type=int, default=PER_CLASS)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--fixed-threshold", type=float, default=None)
    args = parser.parse_args()

    random.seed(args.seed)
    payload, images, by_image, categories, candidates, _ = collect_candidates(
        ANNOTATIONS, TARGETS
    )
    target_category_ids = {
        name: {cid for cid, cname in categories.items() if cname == name}
        for name in TARGETS
    }

    records = []
    for target in TARGETS:
        cat_id = [c["id"] for c in payload["categories"] if c["name"] == target][0]
        large_ids = []
        other_ids = []
        for image_id in candidates[target]:
            img = images[image_id]
            anns = [
                a
                for a in by_image[image_id]
                if a["category_id"] == cat_id and a["iscrowd"] == 0
            ]
            max_area = (
                max(
                    (a["bbox"][2] * a["bbox"][3] / (img["width"] * img["height"]))
                    for a in anns
                )
                if anns
                else 0.0
            )
            if max_area >= 0.05:
                large_ids.append(image_id)
            else:
                other_ids.append(image_id)
        random.shuffle(large_ids)
        sample = large_ids[: args.per_class]
        for image_id in sample:
            records.append(
                {
                    "image_id": image_id,
                    "target": target,
                    "target_category_ids": target_category_ids[target],
                }
            )

    calibration_records = []
    test_records = []
    for target in TARGETS:
        target_records = [record for record in records if record["target"] == target]
        split_index = int(len(target_records) * CALIBRATION_FRACTION)
        calibration_records.extend(target_records[:split_index])
        test_records.extend(target_records[split_index:])

    detector = IngredientDetector()
    with zipfile.ZipFile(IMAGES_ZIP) as images_zip:
        calibration_prepared = {}
        for target in TARGETS:
            target_records = [
                record for record in calibration_records if record["target"] == target
            ]
            calibration_prepared[target] = prepare_records(
                target_records,
                images,
                by_image,
                target_category_ids,
                detector,
                images_zip,
            )
        thresholds = (
            {target: args.fixed_threshold for target in TARGETS}
            if args.fixed_threshold is not None
            else select_thresholds(calibration_prepared, TARGETS)
        )

        test_metrics = {}
        for target in TARGETS:
            target_records = [
                record for record in test_records if record["target"] == target
            ]
            prepared = prepare_records(
                target_records,
                images,
                by_image,
                target_category_ids,
                detector,
                images_zip,
            )
            test_metrics[target] = evaluate_prepared(prepared, thresholds[target])

    low_thresholds = {
        target: max(0.05, round(thresholds[target] * 0.5, 4)) for target in TARGETS
    }
    result = {
        "calibration": {
            "fraction": CALIBRATION_FRACTION,
            "per_class_calibration_images": {
                target: len(
                    [
                        record
                        for record in calibration_records
                        if record["target"] == target
                    ]
                )
                for target in TARGETS
            },
            "per_class_test_images": {
                target: len(
                    [record for record in test_records if record["target"] == target]
                )
                for target in TARGETS
            },
            "thresholds": {key: round(value, 4) for key, value in thresholds.items()},
            "low_thresholds": low_thresholds,
        },
        "test": test_metrics,
        "multi_object_overall": {
            "images": sum(
                item["multi_object"]["images"] for item in test_metrics.values()
            ),
            "both_found_rate": round(
                sum(
                    item["multi_object"]["both_found_rate"]
                    * item["multi_object"]["images"]
                    for item in test_metrics.values()
                )
                / max(
                    sum(
                        item["multi_object"]["images"] for item in test_metrics.values()
                    ),
                    1,
                ),
                4,
            ),
        },
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
