# System Architecture Diagram

## Simple Overview

```
📱 CAMERA → 🧠 AI MODEL → 📶 BLUETOOTH → ⚙️ MOTORS
```

## Detailed Flow

```
┌─────────────────────────────────┐         ┌─────────────────────────────────┐
│          RASPBERRY PI           │         │            EV3 BRICK            │
│                                 │         │                                 │
│  📹 Camera                      │         │                                 │
│      ↓                          │         │                                 │
│  🧠 main.py                     │    📶    │  📡 ev3_bluetooth_server.py     │
│     - Classification Model      │ Bluetooth │      ↓                        │
│     - Detects: plastic, metal,  │ ←────────→│  ⚙️ motor_control.py           │
│       paper, trash, etc.        │         │     - Controls physical motors │
│      ↓                          │         │     - OUTPUT_A: Panel Left     │
│  📶 motor_control_bluetooth.py  │         │     - OUTPUT_B: Panel Right    │
│     - Sends commands via BT     │         │     - OUTPUT_C: Rod Motor       │
│                                 │         │     - OUTPUT_D: Trap Motor      │
└─────────────────────────────────┘         └─────────────────────────────────┘
```

## Step-by-Step Process

```
1. 📹 Camera sees garbage
        ↓
2. 🧠 AI classifies: "plastic"
        ↓
3. 📤 Bluetooth sends: {"action": "classify", "label": "plastic"}
        ↓
4. 📡 EV3 receives command
        ↓
5. ⚙️ Motors execute sequence:
   - Panels shift LEFT (for plastic)
   - Rods extend
   - Trap opens
   - Trash falls
   - Trap closes
   - Rods retract
   - Panels reset
```

## File Roles

```
RASPBERRY PI FILES:
├── main.py                      → Runs camera + AI model
├── motor_control_bluetooth.py   → Sends motor commands via Bluetooth
└── requirements.txt             → Python dependencies

EV3 BRICK FILES:
├── ev3_bluetooth_server.py      → Receives Bluetooth commands
├── motor_control.py             → Controls physical motors
└── (ev3dev OS)                  → Hardware interface
```

## Classification → Motor Mapping

```
🗑️ TRASH TYPES:
┌─────────────────┬─────────────────┬─────────────────┐
│   TRASH TYPE    │  PANEL ACTION   │    OUTCOME      │
├─────────────────┼─────────────────┼─────────────────┤
│ Plastic         │ Shift LEFT      │ Recycling Bin   │
│ Metal           │ Shift LEFT      │ Recycling Bin   │
│ Paper/Cardboard │ Shift LEFT      │ Recycling Bin   │
│ Trash/Garbage   │ Shift RIGHT     │ Trash Bin       │
│ Organic/Compost │ Stay CENTER     │ Compost Bin     │
│ Glass/Battery   │ NO MOVEMENT     │ Rejected        │
└─────────────────┴─────────────────┴─────────────────┘
```

## Communication Protocol

```
COMMAND EXAMPLES:
┌─────────────────────────────────────────────────────────┐
│ Raspberry Pi → EV3:                                     │
│ {"action": "classify", "label": "plastic"}              │
│                                                         │
│ EV3 → Raspberry Pi:                                     │
│ {"status": "success", "message": "Sorted: plastic"}    │
└─────────────────────────────────────────────────────────┘
```

## Physical Setup

```
EV3 BRICK CONNECTIONS:
   ┌─────────────┐
   │     EV3     │
   │   BRICK     │
   └──┬──┬──┬──┬─┘
      A  B  C  D
      │  │  │  │
      │  │  │  └── 🚪 Trap Motor (opens/closes bottom)
      │  │  └───── 📏 Rod Motor (extends/retracts support)
      │  └──────── ↔️ Panel Right Motor
      └─────────── ↔️ Panel Left Motor

SORTING MECHANISM:
        📹 Camera
           │
    ┌──────▼──────┐
    │   Panels    │ ← Move LEFT/RIGHT to direct trash
    │  ←─────→    │
    └─────┬───────┘
          │
    ┌─────▼─────┐
    │   Rods    │ ← Extend to support trash during sorting
    │    |||    │
    └─────┬─────┘
          │
    ┌─────▼─────┐
    │   Trap    │ ← Opens to drop trash into correct bin
    │  ▄▄▄▄▄▄▄  │
    └───────────┘
          │
    ┌─────▼─────┐
    │   Bins    │
    │ 🗑️ 🗑️ 🗑️ │
    └───────────┘
```

This system automatically sorts garbage in real-time using computer vision and robotic control!
