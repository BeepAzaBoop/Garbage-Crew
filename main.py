import argparse
import time
import servo_motor
from servo_motor import sort_to_compost, sort_to_recyclable, sort_to_trash
import cv2
import numpy as np
import torch
import torch.nn as nn
from torchvision import models, transforms
import os


print(torch.__version__)

parser = argparse.ArgumentParser(description="Garbage Classifier")
parser.add_argument(
    "-q", "--quantized", action="store_true", help="Use quantized model"
)
parser.add_argument("-y", "--yolo", action="store_true", help="Enable YOLO detection")
parser.add_argument(
    "-s", "--snapshot", action="store_true", help="Enable snapshot mode"
)
parser.add_argument(
    "-p", "--pretrained", action="store_true", help="Use pretrained model"
)
args = parser.parse_args()

use_quantized = args.quantized
use_yolo = args.yolo
snapshot_mode = args.snapshot
use_pretrained = args.pretrained

# Constants
IMG_SIZE = 224
CLASSES = [
    "battery",
    "glass",
    "metal",
    "organic_waste",
    "paper_cardboard",
    "plastic",
    "textiles",
    "trash",
]

# Mapping of 8 detailed classes to 3 main categories
CLASS_TO_CATEGORY = {
    "battery": "trash",          # Special waste - goes to trash
    "glass": "recyclable",       # Glass is recyclable
    "metal": "recyclable",       # Metal is recyclable
    "organic_waste": "compost",  # Organic waste goes to compost
    "paper_cardboard": "recyclable",  # Paper/cardboard is recyclable
    "plastic": "recyclable",     # Plastic is recyclable
    "textiles": "trash",         # Textiles typically go to trash
    "trash": "trash",            # Trash goes to trash
}

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch.backends.quantized.engine = "qnnpack"
torch.set_num_threads(2)

if use_quantized:
    if use_pretrained:
        model = models.quantization.mobilenet_v3_large(quantize=True, weights="DEFAULT")
        # model.load_state_dict(torch.load("/home/bharathreddy/Downloads/Garbage-Crew/models/mobilenetv3_garbage_classifier_quantized_weights.pt"))
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

# Optional YOLO import and model load
if use_yolo:
    from ultralytics import YOLO

    # yolo_model = YOLO("models/yolov8n.pt")  # Replace with your own model if needed
    yolo_model = YOLO(
        "./models/yolo11n.pt"
    )  # latest YOLOv11 model, pretty much same latency as yolov8 but more accurate
    yolo_model.export(format="torchscript", imgsz=224, device="cpu")

# Preprocessing
# preprocess = transforms.Compose(
    # [
        # transforms.ToPILImage(),
        # transforms.Resize((IMG_SIZE, IMG_SIZE)),
        # transforms.ToTensor(),
        # transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    # ]
# )

def preprocess_cv2(image_bgr):
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    image_resized = cv2.resize(image_rgb, (224, 224))
    image_tensor = torch.from_numpy(image_resized).float() / 255.0
    image_tensor = image_tensor.permute(2, 0, 1)  # HWC to CHW
    image_tensor = transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )(image_tensor)
    return image_tensor.unsqueeze(0)


# Webcam setup
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

    motion_detected = False
    prev_gray = None
    motion_threshold = 500000

    boxes = np.empty((0, 4))
    results = None

    while True:
        # Always read a new frame if not frozen
        if not frozen:
            ret, frame = cap.read()
            if not ret:
                break
            display_frame = frame

            # Motion detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if prev_gray is None:
                prev_gray = gray
                continue

            diff_frame = cv2.absdiff(prev_gray, gray)
            prev_gray = gray

            motion_score = np.sum(diff_frame)
            motion_detected = motion_score > motion_threshold

            cv2.putText(
                display_frame,
                f"Motion: {'Yes' if motion_detected else 'No'}",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2,
            )


        else:
            display_frame = freeze_frame.copy()

        # Only run detection/classification if frozen (snapshot taken), or if not in snapshot mode
        if motion_detected and (not snapshot_mode or frozen):
            if use_yolo:
                if frame_count % 3 == 0:
                    results = yolo_model(display_frame, imgsz=480)[0]
                    boxes = results.boxes.xyxy.cpu().numpy()

                for box in boxes:
                    x1, y1, x2, y2 = map(int, box)
                    obj_crop = display_frame[y1:y2, x1:x2]

                    if obj_crop.size == 0:
                        continue

                    input_tensor = preprocess_cv2(obj_crop).to(DEVICE)
                    outputs = model(input_tensor)
                    pred = torch.argmax(outputs, 1).item()
                    label = CLASSES[pred]
                    
                    # Map the detailed class to one of 3 main categories
                    category = CLASS_TO_CATEGORY[label]
                    
                    # Handle the 3-category sorting (replacing EV3 commands)
                    print(f"Detected: {label} → Category: {category}")
                    if category == "compost":
                        sort_to_compost()
                    elif category == "recyclable":
                        sort_to_recyclable()
                    elif category == "trash":
                        sort_to_trash()

                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(
                        display_frame,
                        f"{label} → {category}",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 255, 0),
                        2,
                    )
            else:
                input_tensor = preprocess_cv2(display_frame).to(DEVICE)
                outputs = model(input_tensor)
                pred = torch.argmax(outputs, 1).item()
                label = CLASSES[pred]
                
                # Map the detailed class to one of 3 main categories
                category = CLASS_TO_CATEGORY[label]
                
                # Handle the 3-category sorting
                print(f"Detected: {label} → Category: {category}")
                if category == "compost":
                    sort_to_compost()
                elif category == "recyclable":
                    sort_to_recyclable()
                elif category == "trash":
                    sort_to_trash()

                cv2.putText(
                    display_frame,
                    f"{label} → {category}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2,
                )

        # FPS calculation
        frame_count += 1
        current_time = time.time()
        if current_time - last_fps_time >= 1.0:
            fps = frame_count / (current_time - last_fps_time)
            last_fps_time = current_time
            frame_count = 0

        # Draw FPS on frame
        cv2.putText(
            display_frame,
            f"FPS: {fps:.1f}",
            (10, display_frame.shape[0] - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 0),
            2,
        )
        
        # display_large = cv2.resize(display_frame, (600, 480))  # or any size you want
        cv2.imshow("Garbage Classifier", display_frame)

        key = cv2.waitKey(1)

        if snapshot_mode:
            if key == ord("s") and not frozen:
                freeze_frame = frame.copy()
                frozen = True
            elif key == ord("r") and frozen:
                frozen = False
                freeze_frame = None

        if key == ord("q"):
            break


cap.release()
cv2.destroyAllWindows()
