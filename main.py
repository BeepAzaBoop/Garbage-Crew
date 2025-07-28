import argparse
import time
import servo_motor
from servo_motor import sort_to_compost, sort_to_recyclable, sort_to_trash
import cv2
import numpy as np
import torch
import torch.nn as nn
from torchvision import models, transforms

print(torch.__version__)

parser = argparse.ArgumentParser(description="Garbage Classifier")
parser.add_argument("-q", "--quantized", action="store_true", help="Use quantized model")
parser.add_argument("-y", "--yolo", action="store_true", help="Enable YOLO detection")
parser.add_argument("-s", "--snapshot", action="store_true", help="Enable snapshot mode")
parser.add_argument("-p", "--pretrained", action="store_true", help="Use pretrained model")
args = parser.parse_args()

use_quantized = args.quantized
use_yolo = args.yolo
snapshot_mode = args.snapshot
use_pretrained = args.pretrained

IMG_SIZE = 224
CLASSES = [
    "battery", "glass", "metal", "organic_waste",
    "paper_cardboard", "plastic", "textiles", "trash"
]

CLASS_TO_CATEGORY = {
    "battery": "trash",
    "glass": "trash",
    "metal": "recyclable",
    "organic_waste": "compost",
    "paper_cardboard": "recyclable",
    "plastic": "recyclable",
    "textiles": "trash",
    "trash": "trash",
}

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch.backends.quantized.engine = "qnnpack"
torch.set_num_threads(2)

if use_quantized:
    if use_pretrained:
        model = models.quantization.mobilenet_v3_large(quantize=True, weights="DEFAULT")
        model.classifier[3] = nn.quantized.Linear(1280, len(CLASSES))
        model = torch.jit.script(model)
    else:
        model = torch.jit.load("./models/mobilenetv3_quantized_scripted.pt", map_location="cpu")
else:
    if use_pretrained:
        model = models.mobilenet_v3_large(weights="DEFAULT")
        model.classifier[3] = nn.Linear(1280, len(CLASSES))
    else:
        model = torch.load(
           "./models/mobilenetv3_garbage_classifier.pt",
            map_location=DEVICE,
            weights_only=False,
        )
    model = torch.jit.script(model)

model = torch.jit.optimize_for_inference(model)
model.to(DEVICE)
model.eval()

if use_yolo:
    from ultralytics import YOLO
    yolo_model = YOLO("./models/yolo11n.pt")

def preprocess_cv2(image_bgr):
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    image_resized = cv2.resize(image_rgb, (224, 224))
    image_tensor = torch.from_numpy(image_resized).float() / 255.0
    image_tensor = image_tensor.permute(2, 0, 1)
    image_tensor = transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )(image_tensor)
    return image_tensor.unsqueeze(0)

def draw_text_with_background(img, text, org, font, scale, text_color, bg_color, alpha=0.45, thickness=2, padding=5):
    text_size, _ = cv2.getTextSize(text, font, scale, thickness)
    x, y = org
    w, h = text_size
    x1, y1 = x - padding, y - h - padding
    x2, y2 = x + w + padding, y + padding

    overlay = img.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), bg_color, -1)
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
    cv2.putText(img, text, org, font, scale, text_color, thickness, cv2.LINE_AA)

cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 600)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 36)

if not cap.isOpened():
    raise IOError("Webcam not accessible")

print("\nPress 'q' to quit.")
if snapshot_mode:
    print("Press 's' to take snapshot, 'r' to reset live view.\n")

with torch.no_grad():
    frozen = False
    freeze_frame = None

    frame_count = 0
    last_fps_time = time.time()
    fps = 0.0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frozen:
            display_frame = freeze_frame.copy()
        else:
            display_frame = frame.copy()

        current_time = time.time()
        frame_count += 1
        if current_time - last_fps_time >= 1.0:
            fps = frame_count / (current_time - last_fps_time)
            frame_count = 0
            last_fps_time = current_time


        if frozen and snapshot_mode and not classified:
            input_tensor = preprocess_cv2(freeze_frame).to(DEVICE)
            outputs = model(input_tensor)
            pred = torch.argmax(outputs, 1).item()
            label = CLASSES[pred]
            category = CLASS_TO_CATEGORY[label]

            print(f"Detected: {label} → Category: {category}")
            if category == "compost":
                sort_to_compost()
            elif category == "recyclable":
                sort_to_recyclable()
            elif category == "trash":
                sort_to_trash()

            result_text = f"{label} - {category}"
            classified = True
        elif frozen and snapshot_mode and classified:
            draw_text_with_background(
                display_frame,
                text=result_text,
                org=(10, 32),              # position with padding
                font=cv2.FONT_HERSHEY_SIMPLEX,
                scale=1.0,
                text_color=(255, 255, 255),  # white text
                bg_color=(0, 0, 0),           # black translucent background
                thickness=2
            )

        draw_text_with_background(
            display_frame,
            text=f"FPS: {fps:.1f}",
            org=(10, display_frame.shape[0] - 10),
            font=cv2.FONT_HERSHEY_SIMPLEX,
            scale=0.8,
            text_color=(255, 255, 255),  # white text
            bg_color=(0, 0, 0),           # black translucent background
            alpha=0.3
        )

        cv2.imshow("Garbage Classifier", display_frame)
        key = cv2.waitKey(1)

        if snapshot_mode:
            if key == ord("s") and not frozen:
                freeze_frame = frame.copy()
                frozen = True
                classified = False  # allow classification again
            elif key == ord("r") and frozen:
                frozen = False
                freeze_frame = None
                classified = False

        if key == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()