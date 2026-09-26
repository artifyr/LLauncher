# Llauncher

Lightweight hardware tuner, profile manager, and local model inference launcher for llama.cpp (`llama-server.exe`).

---

## Overview

Llauncher is a native Windows desktop controller designed for managing local Large Language Model (LLM) server instances powered by `llama.cpp`. Built on CustomTkinter, Llauncher provides a compact, low-latency dashboard to configure hardware acceleration, context limits, memory quantization, and sampling parameters without command-line overhead.

It includes dedicated hardware optimizations tuned for modern high-VRAM GPUs, specifically the AMD Radeon RX 9070 XT (16 GB VRAM) paired with 32 GB system RAM under Vulkan.

---

## Key Features

- Compact 3-Column Dashboard: Engineered with a horizontal layout to prevent vertical scrolling and eliminate resizing lag.
- Automatic GPU Device Detection: Automatically identifies Vulkan, CUDA, and CPU compute devices directly from the `llama-server.exe` binary.
- Real-Time Parameter Sliders:
  - GPU Layers (`-ngl`): 0 to 99 layers (supports full offload or partial CPU split).
  - Context Window (`-c`): Stepped range from 2,048 tokens up to 131,072 tokens (128K).
  - Batch Size (`-b`): Incremental ladder (128, 256, 512, 1024, 2048, 4096).
  - Micro-Batch Size (`-ub`): Incremental ladder (128, 256, 512, 1024, 2048).
  - KV Cache Precision (`-ctk` / `-ctv`): Dropdown selection for `q8_0`, `q4_0`, `q4_1`, and lossless `f16`.
- 3-Slot Profile System:
  - Includes three pre-configured profiles: Balanced, Max Quality, and Max Performance.
  - Instantly swaps inference parameters across models without modifying selected model paths.
  - Save adjustments directly to the active profile with instant persistent storage in `profiles.json`.
  - Built-in profile renaming tool to customize profiles to specific workloads.
- RX 9070 XT and 32 GB RAM Optimization Suite:
  - RAM Locking (`--load-mode mlock`): Pins weights and context in system memory to eliminate Windows pagefile swapping.
  - Batch Processing Threads (`-tb`): Accelerates CPU prompt ingestion during pre-fill.
  - VRAM Headroom Target (`--fit-target`): Reserves a dedicated VRAM safety margin to prevent driver timeouts (TDR).
  - KV Cache Reuse (`--cache-reuse`): Reuses pre-computed prefix tokens across multi-turn chats.
  - Dedicated Server Slot (`-np 1`): Allocates full GPU resources to single-session inference.
  - RAM Cache Allocation (`--cache-ram`): Utilizes excess system RAM for context cache overflow.
- Vision Projector Support (`--mmproj`): Integrated Vision checkbox dynamically reveals mmproj weights picker and automatically attaches `--mmproj` for multimodal/vision inference.
- Live Server Lifecycle Management: One-click Start / Stop server toggle button with live process health tracking and clean process tree termination.
- Vulkan Memory Stability: Automatically prepends `GGML_VK_DISABLE_PINNED=1` to prevent driver allocation faults on AMD hardware.

---

## Hardware Profiles Reference

| Parameter | Balanced (Default) | Max Quality | Max Performance |
| :--- | :--- | :--- | :--- |
| Target Use Case | General reasoning, coding, chat | Lossless recall, critical accuracy | Ultra-fast token generation |
| GPU Layers (`-ngl`) | 99 (All) | 99 (All) | 99 (All) |
| Context Size (`-c`) | 131,072 (128K) | 131,072 (128K) | 32,768 (32K) |
| Batch Size (`-b`) | 1024 | 1024 | 2048 |
| Micro-Batch (`-ub`) | 256 | 256 | 512 |
| KV Cache K / V | q8_0 / q8_0 | f16 / f16 | q4_0 / q4_0 |
| Temperature / Top-P | 0.5 / 0.95 | 0.7 / 0.95 | 0.5 / 0.90 |
| Flash Attention (`-fa`) | Enabled | Enabled | Enabled |
| Jinja Templates (`--jinja`) | Enabled | Enabled | Enabled |
| Memory Lock (`--load-mode`) | Off | Enabled (`mlock`) | Enabled (`mlock`) |
| Prompt Threads (`-tb`) | Off | Off | Enabled (`8`) |
| VRAM Headroom (`--fit-target`) | Off | Enabled (`1024 MiB`) | Enabled (`1024 MiB`) |
| Dedicated Slot (`-np`) | Off | Off | Enabled (`1`) |
| KV Cache Reuse | Off | Enabled (`256`) | Enabled (`256`) |

---

## System Requirements

- Operating System: Windows 10 or Windows 11 (64-bit)
- Python Version: Python 3.10, 3.11, 3.12, 3.13, or 3.14
- Dependencies: `customtkinter`, `pywinstyles`
- Backend Engine: `llama-server.exe` from a recent release of `llama.cpp`

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/Llauncher.git
cd Llauncher
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

To compile Llauncher into a single standalone `.exe` without console windows and bundled with application icons and CustomTkinter assets:

### 1. Install PyInstaller

```bash
pip install pyinstaller
```

### 2. Run the Build Command

```bash
pyinstaller --noconsole --onefile --clean \
    --name="Llauncher" \
    --icon="llauncher.ico" \
    --add-data="llauncher.ico;." \
    --collect-all customtkinter \
    --exclude-module matplotlib \
    --exclude-module scipy \
    --exclude-module pandas \
    --exclude-module torch \
    --exclude-module IPython \
    --exclude-module notebook \
    launcher.py
```

The resulting binary will be output to the `dist/` directory as `Llauncher.exe` (approximately 15 MB).

---

## File Structure

```
Llauncher/
|-- launcher.py        # Main application source code
|-- llauncher.ico      # Application and executable icon
|-- profiles.json      # Persistent profile storage (auto-generated)
|-- requirements.txt   # Python package dependencies
|-- README.md          # Project documentation
\-- dist/
    \-- Llauncher.exe  # Standalone Windows executable
```

---

## License

This project is open-source and available under the MIT License.
