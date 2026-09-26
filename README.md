# Llauncher

Lightweight hardware tuner, profile manager, and local model inference launcher for llama.cpp (`llama-server.exe`).

---

## Overview

**Llauncher** is a native Windows desktop controller designed for orchestrating local Large Language Model (LLM) server instances powered by `llama.cpp`. Built on CustomTkinter and styled with native Windows 11 Mica material, Llauncher provides an ultra-responsive, zero-latency dashboard to configure hardware acceleration, context limits, KV cache quantization, sampling parameters, multimodal vision projectors, and inference profiles without manual command-line overhead.

It includes dedicated hardware optimizations tuned for modern high-VRAM GPUs, specifically the AMD Radeon RX 9070 XT (16 GB VRAM) paired with 32 GB system RAM under Vulkan, while seamlessly supporting CUDA and CPU-only inference.

---

## Key Features

- **Windows 11 Native Mica Styling & Minimalist Aesthetic**:
  - Immersive dark mode with native Windows 11 Mica translucency effect and dark title bar.
  - High-contrast, clean off-white primary action controls paired with dark slate cards and muted borders.
  - Off-screen buffer staging eliminates initial render flickering or geometry stutter.

- **Model & Library Management**:
  - **Recent Models History & Fast Switching**: Built-in dropdown storing up to 15 recently selected or launched `.gguf` weight files with automatic deduplication, persistent storage in `recent_models.json`, and one-click history clearing.
  - **Auto-Detect Vision Projector (`mmproj`)**: Automatically detects multimodal vision models (e.g. Qwen2-VL, LLaVA, MiniCPM, Ovis, InternVL, Pixtral) and scans the model folder to locate, auto-check, and attach the matching `mmproj*.gguf` multimodal projector file.

- **Compact 3-Column Dashboard**:
  - Horizontally aligned layout engineered to completely eliminate vertical scrolling and resizing lag across standard display resolutions.

- **Automatic GPU Device Detection**:
  - Asynchronously queries `llama-server.exe` to discover available compute devices (Vulkan devices, CUDA devices, and CPU-only fallback) without freezing the UI or popping up transient console windows.

- **Real-Time Parameter Sliders & Badges**:
  - **GPU Layers (`-ngl`)**: 0 to 99 layers (supports full offload or partial CPU split).
  - **Context Window (`-c`)**: Stepped range from 2,048 tokens up to 131,072 tokens (128K).
  - **Batch Size (`-b`)**: Incremental ladder (128, 256, 512, 1024, 2048, 4096).
  - **Micro-Batch Size (`-ub`)**: Incremental ladder (128, 256, 512, 1024, 2048).
  - **KV Cache Precision (`-ctk` / `-ctv`)**: Dropdown selection for `q8_0`, `q4_0`, `q4_1`, and lossless `f16`.

- **3-Slot Persistent Profile System**:
  - Pre-configured profiles: **Balanced**, **Max Quality**, and **Max Performance**.
  - Instantly swaps hardware and generation settings across models without altering selected model paths.
  - Save adjustments directly to the active profile with instant persistent storage in `profiles.json`.
  - Built-in modal dialog to rename and personalize profile slots to custom workloads.

- **RX 9070 XT & 32 GB RAM Optimization Suite**:
  - **RAM Locking (`--load-mode mlock`)**: Pins weights and context in system memory to eliminate Windows pagefile swapping.
  - **Prompt Batch Processing Threads (`-tb`)**: Accelerates CPU prompt ingestion during pre-fill.
  - **VRAM Headroom Target (`--fit-target`)**: Reserves a dedicated VRAM safety margin to prevent driver timeouts (TDR).
  - **KV Cache Reuse (`--cache-reuse`)**: Reuses pre-computed prefix tokens across multi-turn chats.
  - **Dedicated Server Slot (`-np 1`)**: Allocates full GPU resources to single-session inference.
  - **RAM Cache Allocation (`--cache-ram`)**: Utilizes excess system RAM for context cache overflow.

- **Multimodal Vision Model Support (`--mmproj`)**:
  - Vision toggle reveals dedicated projector weights path and automatically injects `--mmproj` arguments into the launch command.

- **Live Server Lifecycle & Process Management**:
  - Dual-state Start / Stop action button with real-time status polling.
  - Switches to a crimson danger button (`🛑 Stop Model Server`) once online.
  - Safe child process tree termination (`taskkill /F /T /PID`) cleanly closes background server and console windows on stop or window close.

- **Vulkan Memory Stability**:
  - Automatically injects `GGML_VK_DISABLE_PINNED=1` into the server process environment to prevent driver memory allocation crashes on AMD Radeon GPUs.

---

## Hardware Profiles Reference

| Parameter | Balanced (Default) | Max Quality | Max Performance |
| :--- | :--- | :--- | :--- |
| **Target Use Case** | General reasoning, coding, chat | Lossless recall, critical accuracy | Ultra-fast token generation |
| **GPU Layers (`-ngl`)** | 99 (All) | 99 (All) | 99 (All) |
| **Context Size (`-c`)** | 131,072 (128K) | 131,072 (128K) | 32,768 (32K) |
| **Batch Size (`-b`)** | 1024 | 1024 | 2048 |
| **Micro-Batch (`-ub`)** | 256 | 256 | 512 |
| **KV Cache K / V** | q8_0 / q8_0 | f16 / f16 | q4_0 / q4_0 |
| **Temperature / Top-P** | 0.5 / 0.95 | 0.7 / 0.95 | 0.5 / 0.90 |
| **Flash Attention (`-fa`)** | Enabled | Enabled | Enabled |
| **Jinja Templates (`--jinja`)** | Enabled | Enabled | Enabled |
| **Memory Lock (`--load-mode`)** | Off | Enabled (`mlock`) | Enabled (`mlock`) |
| **Prompt Threads (`-tb`)** | Off | Off | Enabled (`8`) |
| **VRAM Headroom (`--fit-target`)**| Off | Enabled (`1024 MiB`) | Enabled (`1024 MiB`) |
| **Dedicated Slot (`-np`)** | Off | Off | Enabled (`1`) |
| **KV Cache Reuse** | Off | Enabled (`256`) | Enabled (`256`) |

---

## System Requirements

- **Operating System**: Windows 10 or Windows 11 (64-bit, Windows 11 recommended for Mica effect)
- **Python Version**: Python 3.10 to 3.14
- **Dependencies**: `customtkinter`, `pywinstyles`
- **Backend Engine**: `llama-server.exe` from a recent release of [`llama.cpp`](https://github.com/ggml-org/llama.cpp)

---

## Installation & Running from Source

### 1. Clone the Repository

```bash
git clone https://github.com/artifyr/LLauncher.git
cd LLauncher
```

### 2. Install Required Python Packages

```bash
pip install customtkinter pywinstyles
```

### 3. Launch Application

```bash
python launcher.py
```

---

## Building a Standalone Executable

To compile Llauncher into a single standalone `.exe` using PyInstaller:

```bash
pyinstaller --clean Llauncher.spec
```

The resulting binary will be output to the `dist/` directory as `LLauncher.exe`.

---

## File Structure

```
LLauncher/
|-- assets/
|   |-- logoClear.png      # Header brand logo
|   \-- llauncher.ico      # Window & application icon
|-- dist/
|   \-- LLauncher.exe      # Compiled standalone Windows executable
|-- launcher.py            # Main application source code
|-- Llauncher.spec         # PyInstaller build specification
|-- profiles.json          # Persistent profiles configuration (auto-generated)
|-- recent_models.json     # Persistent recent models history (auto-generated)
|-- README.md              # Project documentation
\-- .gitignore             # Git ignore rules
```

---

## License

This project is open-source and available under the [MIT License](LICENSE).
