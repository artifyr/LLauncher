# Llauncher

Lightweight hardware tuner, profile manager, and local inference controller for llama.cpp (`llama-server.exe`).

[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?logo=windows&logoColor=white)](https://microsoft.com)
[![Python](https://img.shields.io/badge/Python-3.10%20--%203.14-3776AB?logo=python&logoColor=white)](https://python.org)
[![Backend](https://img.shields.io/badge/Backend-llama.cpp-yellow)](https://github.com/ggml-org/llama.cpp)
[![Acceleration](https://img.shields.io/badge/Acceleration-Vulkan%20%7C%20CUDA%20%7C%20CPU-ED1C24)](https://www.vulkan.org)
[![GUI](https://img.shields.io/badge/GUI-CustomTkinter-blue)](https://github.com/TomSchimansky/CustomTkinter)
[![Style](https://img.shields.io/badge/Style-Windows%2011%20Mica-gray)](https://github.com/avalon60/pywinstyles)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Overview

**Llauncher** is a native Windows controller for orchestrating local Large Language Model (LLM) instances powered by `llama.cpp`. Built with CustomTkinter and native Windows 11 Mica material, Llauncher provides a zero-latency interface to configure hardware offloading, context windows, KV cache quantization, sampling parameters, vision projectors, and persistent profiles without manual command-line overhead.

Tuned for high-VRAM hardware, including AMD Radeon RX 9070 XT (16 GB VRAM) paired with 32 GB system RAM under Vulkan, with full support for NVIDIA CUDA and CPU-only inference.

---

## Core Capabilities

- **Windows 11 Mica Interface**: Native dark-mode styling with translucent Mica material, high-contrast off-white controls, and off-screen staging to eliminate launch flicker.
- **Model Library & Vision Auto-Detect**: 15-model history with fast switching, automatic multimodal detection, and auto-attachment of matching `mmproj` vision files.
- **System Tray Integration**: Background notification tray minimization with a right-click menu to show, hide, start, stop, restart, view logs, export/import, or exit.
- **Embedded Log Console**: Expandable in-window drawer streaming real-time stdout/stderr output from `llama-server.exe` with regex/keyword filtering, auto-scroll, and log copying.
- **Auto-Restart Watchdog**: Background watchdog that automatically restarts the server within 2 seconds of an unexpected crash or driver timeout, guarded by a 5-attempt circuit breaker.
- **Export & Import PowerShell Settings**: One-click export to standalone executable `.ps1` or `.bat` scripts with embedded metadata, plus instant import to restore all UI fields from any script.
- **Frontend Integrations & API Tester**: Pre-formatted snippets for Open WebUI, SillyTavern, Continue/Cline, and Hermes Agent, plus an integrated endpoint health checker for `/v1/models` and `/v1/chat/completions`.
- **3-Slot Hardware Profiles**: Instant switching between Balanced, Max Quality, and Max Performance profiles, with in-place saving and custom profile renaming.
- **Vulkan Driver Stability**: Automatically injects `GGML_VK_DISABLE_PINNED=1` into the engine environment to prevent GPU driver memory allocation faults.

---

## Parameter Reference

### Core Arguments
- **`-m` (Model File)**: Filepath to the GGUF model weights on disk.
- **`--mmproj` (Vision Projector)**: Filepath to the companion multimodal projector weights for vision models.
- **`--device` (Compute Device)**: Hardware acceleration backend target (`Vulkan0`, `Vulkan1`, `CUDA0`, or `none`).
- **`-ngl` (GPU Offload Layers)**: Number of model layers offloaded to GPU VRAM (0 for CPU only, up to 99 for complete offload).
- **`-c` (Context Size)**: Total token context window capacity (from 2,048 up to 131,072 tokens).
- **`-b` (Batch Size)**: Logical batch size for parallel prompt evaluation and generation (128 to 4096).
- **`-ub` (Micro-Batch Size)**: Physical batch size processed simultaneously on hardware per compute step (128 to 2048).
- **`-t` (Threads)**: Number of CPU execution threads allocated during generation.
- **`--port` (Server Port)**: Local HTTP listener port for the OpenAI-compatible REST API (default `8082`).
- **`-ctk` (K Cache Precision)**: Quantization format for Key tensors in KV cache memory (`q8_0`, `q4_0`, `q4_1`, `f16`).
- **`-ctv` (V Cache Precision)**: Quantization format for Value tensors in KV cache memory (`q8_0`, `q4_0`, `q4_1`, `f16`).
- **`--temp` (Temperature)**: Randomness scaling factor applied to token logits during sampling.
- **`--top-p` (Top-P)**: Cumulative probability threshold for nucleus sampling.
- **`--min-p` (Min-P)**: Minimum probability cutoff relative to the probability of the most likely token.
- **`-fa` (Flash Attention)**: Hardware-accelerated memory-efficient attention mechanism.
- **`--jinja` (Jinja Templates)**: Enables native chat templating for formatted prompts, function calling, and tools.

### Hardware & Optimization Flags
- **`--load-mode mlock`**: Pins model weights and KV memory in physical RAM to prevent Windows pagefile swapping.
- **`-tb` (Prompt Threads)**: Dedicated CPU threads used to accelerate prompt ingestion and pre-fill processing.
- **`--fit-target` (VRAM Headroom)**: Reserves a safety margin of VRAM (in MiB) to avoid driver timeouts and out-of-memory errors.
- **`--cache-reuse`**: Retains and reuses pre-computed KV tokens across multi-turn conversational exchanges.
- **`-np` (Dedicated Slot)**: Restricts the server to a single dedicated slot to maximize per-user inference throughput.
- **`--cache-ram`**: Allocates surplus system RAM (in MiB) for context cache overflow beyond VRAM capacity.
- **`--n-cpu-moe`**: Offloads a specified count of MoE expert layers to CPU/RAM to fit massive Mixture-of-Experts models.

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

## Quickstart (No Python Required)

To run Llauncher without installing Python or dependencies:

### 1. Download LLauncher
Download `LLauncher.exe` from the [Releases](https://github.com/artifyr/LLauncher/releases) page (or grab `dist/LLauncher.exe` from this repository).

### 2. Download llama.cpp (`llama-server.exe`)
1. Visit the [llama.cpp Releases](https://github.com/ggml-org/llama.cpp/releases) page.
2. Download the pre-built Windows zip archive matching your graphics hardware:
   - **AMD Radeon**: `llama-bXXXX-bin-win-vulkan-x64.zip`
   - **NVIDIA GeForce / RTX**: `llama-bXXXX-bin-win-cuda-cuXX.X-x64.zip`
   - **Intel / CPU Only**: `llama-bXXXX-bin-win-cpu-x64.zip`
3. Extract the zip to any folder (e.g. `C:\Tools\llama.cpp\`). Locate `llama-server.exe` inside.

### 3. Download a GGUF Model
Download any `.gguf` quantized model from Hugging Face (e.g. models by `bartowski`, `Qwen`, or `TheBloke`). For multimodal vision models, also download the matching `mmproj-*.gguf` file to the same folder.

### 4. Run Llauncher
1. Double-click `LLauncher.exe`.
2. Click **Browse** next to **llama-server.exe** and select your executable.
3. Click **Browse** next to **Model GGUF** and select your model file.
4. Click **Start Model Server**.
5. Once running, click **Open Web UI** to chat in your browser, or click **Client Configs** to connect frontend apps.

---

## Running from Source

```bash
# 1. Clone repository
git clone https://github.com/artifyr/LLauncher.git
cd LLauncher

# 2. Install dependencies
pip install customtkinter pywinstyles pystray pillow

# 3. Launch application
python launcher.py
```

---

## Building Standalone Executable

Compile Llauncher into a single standalone `.exe` using PyInstaller:

```bash
pyinstaller --clean Llauncher.spec
```

The resulting executable is generated at `dist/LLauncher.exe`.

---

## Universal VRAM Profiles (Manual Import)

LLauncher includes pre-configured, optimized profile scripts located in the `profiles/` folder. These profiles are designed for hardware compatibility across common VRAM capacities and are **imported manually** (not loaded by default). MoE layer offloading (`--n-cpu-moe`) is disabled in these profiles by default for universal compatibility across dense and MoE models.

To import a profile:
1. In LLauncher, click **Import .ps1** in the footer.
2. Navigate to `profiles/` and select the profile matching your GPU VRAM:

| Profile Script | Target Hardware | Recommended Context (`-c`) | Batch (`-b` / `-ub`) | Cache Type | Key Optimizations |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `profile_4gb_vram.ps1` | 4 GB VRAM (GTX 1650, RTX 3050 mobile, etc.) | 8,192 tokens | 512 / 128 | `q4_0` | Memory conservative, `--fit-target 256` |
| `profile_8gb_vram.ps1` | 8 GB VRAM (RTX 3070, 4060, RX 6600, etc.) | 16,384 tokens | 512 / 256 | `q4_0` | `-ngl 99`, `--fit-target 512` |
| `profile_12gb_vram.ps1` | 12 GB VRAM (RTX 3060 12GB, 4070, RX 6700 XT) | 32,768 tokens | 1024 / 256 | `q8_0` | High throughput, `q8_0` KV, `--fit-target 768` |
| `profile_16gb_vram.ps1` | 16 GB VRAM (RTX 4080, RX 7800 XT, etc.) | 65,536 tokens | 1024 / 256 | `q8_0` | Extended context, high batch throughput |
| `profile_24gb_vram.ps1` | 24 GB+ VRAM (RTX 3090, RTX 4090, Workstations) | 131,072 tokens | 2048 / 512 | `q8_0` | Maximum context, `mlock`, RAM cache reservation |

*Note: You can also execute these `.ps1` files directly in PowerShell to launch your llama-server headlessly.*

---

## File Structure

```
LLauncher/
|-- assets/
|   |-- Logo.png           # Header brand logo
|   \-- llauncher.ico      # Application and tray icon
|-- dist/
|   \-- LLauncher.exe      # Compiled standalone Windows executable
|-- profiles/              # Universal VRAM hardware preset scripts (manual import)
|   |-- profile_4gb_vram.ps1
|   |-- profile_8gb_vram.ps1
|   |-- profile_12gb_vram.ps1
|   |-- profile_16gb_vram.ps1
|   \-- profile_24gb_vram.ps1
|-- launcher.py            # Main application source code
|-- Llauncher.spec         # PyInstaller build specification
|-- profiles.json          # Persistent profiles configuration
|-- recent_models.json     # Persistent recent models history
|-- README.md              # Project documentation
\-- .gitignore             # Git ignore rules
```

---

## License

This project is open-source under the [MIT License](LICENSE).
