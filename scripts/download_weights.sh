#!/bin/bash
# scripts/download_weights.sh
# Downloads YOLO and SAM 2 model weights into data/model_weights/

set -e

WEIGHTS_DIR="data/model_weights"
mkdir -p $WEIGHTS_DIR

echo "Downloading YOLOv10x weights..."
# YOLOv10 — downloaded automatically by ultralytics on first use
# Manually cache it:
python -c "from ultralytics import YOLO; YOLO('yolov10x.pt')"
cp ~/.config/Ultralytics/yolov10x.pt $WEIGHTS_DIR/ 2>/dev/null || true

echo "Downloading SAM 2 weights..."
# SAM 2 Large
wget -q --show-progress \
  https://dl.fbaipublicfiles.com/segment_anything_2/072824/sam2_hiera_large.pt \
  -O $WEIGHTS_DIR/sam2_hiera_large.pt

echo "All weights downloaded to $WEIGHTS_DIR/"
ls -lh $WEIGHTS_DIR/
