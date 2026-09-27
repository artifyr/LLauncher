# Llauncher

Lightweight hardware tuner, profile manager, and local inference controller for llama.cpp (`llama-server.exe`).

[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?logo=windows&logoColor=white)](https://microsoft.com)
[![Python](https://img.shields.io/badge/Python-3.10%20--%203.14-3776AB?logo=python&logoColor=white)](https://python.org)
[![Backend](https://img.shields.io/badge/Backend-llama.cpp-yellow)](https://github.com/ggml-org/llama.cpp)
[![Acceleration](https://img.shields.io/badge/Acceleration-Vulkan%20%7C%20CUDA%20%7C%20CPU-ED1C24)](https://www.vulkan.org)
[![GUI](https://img.shields.io/badge/GUI-CustomTkinter-blue)](https://github.com/TomSchimansky/CustomTkinter)
[![Style](https://img.shields.io/badge/Style-Windows%2011%20Mica-gray)](https://github.com/avalon60/pywinstyles)
[![License](https://img.shields.io/badge/License-GPL%203.0-blue.svg)](LICENSE)

---

### Overview

<sub>**Llauncher** is a native, standalone Windows controller for local Large Language Model (LLM) instances powered by `llama.cpp`. Built with CustomTkinter and Windows 11 Mica material, Llauncher provides a zero-latency interface to configure hardware offloading, context windows, KV cache quantization, sampling parameters, vision projectors, and persistent profiles without manual command-line overhead. Supports AMD Vulkan, NVIDIA CUDA, and CPU-only inference.</sub>

> [!NOTE]
> <sub>**Zero Installation Required**: Llauncher is completely portable. Simply download `LLauncher.exe`, run it anywhere, and you're ready to go—no installer, no dependencies, and no background services.</sub>

---

### Core Capabilities

<sub>

- **Zero-Install Standalone Portability**: Completely self-contained executable with zero setup or runtime installer needed.
- **Windows 11 Mica Interface**: Native dark-mode styling with translucent Mica material and zero launch flicker.
- **Hugging Face GGUF Downloader**: Search repos, explore quantizations with file sizes, and perform chunked resumable downloads directly into your configured Models folder.
- **llama.cpp Binary Updater**: One-click in-app updater that checks GitHub releases, matches your GPU backend (Vulkan/CUDA/CPU), and extracts new binaries to `bin/`.
- **Pre-Launch VRAM Memory Estimator & Auto-Fit**: Real-time projected VRAM and RAM safety meters with a one-click **⚡ Auto-Fit** button to maximize layer offload and context window without OOM risk.
- **Live Inference Telemetry Dashboard**: Real-time status bar streaming prompt eval speed (tokens/sec), generation speed (tokens/sec), total token counters, and slot saturation.
- **Instant Secure Public Tunneling**: Built-in manager for Ngrok and Cloudflare Quick Tunnel (`cloudflared`) to expose `llama-server` over public HTTPS for mobile devices, remote web UIs, and external APIs with zero port forwarding.
- **Context Shift & Auto-Compaction**: Continuous sliding context (`--ctx-shift`) to prevent token-overflow halts, plus automated KV cache defragmentation (`--defrag-thold`).
- **Model Library & Vision Auto-Detect**: 15-model history with fast switching, multi-part GGUF split detection (`00001-of-00004`), and automatic `mmproj` vision attachment.
- **System Tray Integration**: Background tray minimization with full right-click control menu.
- **Embedded Log Console**: Expandable drawer streaming real-time stdout/stderr with regex/keyword filter, auto-scroll, and copy.
- **Auto-Restart Watchdog**: Background watchdog restarting the server within 2 seconds of a crash (5-attempt circuit breaker).
- **Export & Import PowerShell Settings**: One-click export to executable `.ps1` or `.bat` scripts, plus instant import.
- **AI Profile Helper**: Built-in generator to enter multi-GPU (GPU_1 to GPU_4), CPU, RAM, and model specs to copy an optimization prompt for Grok, ChatGPT, Claude, and other LLMs.
- **Frontend Integrations & API Tester**: One-click config snippets for Open WebUI, SillyTavern, Continue/Cline, and Hermes Agent, plus an integrated endpoint tester.
- **3-Slot Hardware Profiles**: Fast switching between Balanced, Max Quality, and Max Performance with in-place saving and renaming.
- **Vulkan Driver Stability**: Injects `GGML_VK_DISABLE_PINNED=1` to prevent GPU driver memory allocation faults.

</sub>

---

### Parameter Reference

#### Core Arguments
<sub>

- **`-m`**: Filepath to GGUF model weights.
- **`--mmproj`**: Filepath to companion multimodal projector weights for vision models.
- **`--device`**: Acceleration backend target (`Vulkan0`, `Vulkan1`, `CUDA0`, or `none`).
- **`-ngl`**: Model layers offloaded to GPU VRAM (0 for CPU, 99 for complete offload).
- **`-c`**: Total token context window capacity (2,048 to 131,072 tokens).
- **`-b`**: Logical batch size for parallel prompt evaluation (128 to 4096).
- **`-ub`**: Physical micro-batch size processed simultaneously on hardware (128 to 2048).
- **`-t`**: CPU execution threads allocated during generation.
- **`--port`**: Local HTTP listener port for OpenAI-compatible REST API (default `8082`).
- **`-ctk` / `-ctv`**: KV cache quantization precision (`q8_0`, `q4_0`, `q4_1`, `f16`).
- **`--temp` / `--top-p` / `--min-p`**: Sampling randomness and nucleus cutoff thresholds.
- **`-fa`**: Hardware-accelerated Flash Attention.
- **`--jinja`**: Native chat templating for formatted prompts and function calling.

</sub>

#### Hardware & Optimization Flags
<sub>

- **`--ctx-shift`**: Enables continuous rolling context shift when context limit is reached instead of halting.
- **`--defrag-thold`**: Threshold for automated KV cache memory defragmentation and compaction (e.g. `0.1`).
- **`--load-mode mlock`**: Pins model weights and KV memory in physical RAM to prevent pagefile swapping.
- **`-tb`**: Dedicated CPU threads used to accelerate prompt ingestion and pre-fill processing.
- **`--fit-target`**: Reserves a VRAM safety margin (in MiB) to avoid driver out-of-memory errors.
- **`--cache-reuse`**: Retains and reuses pre-computed KV tokens across multi-turn exchanges.
- **`-np`**: Restricts the server to a single dedicated slot to maximize per-user throughput.
- **`--cache-ram`**: Allocates surplus system RAM (in MiB) for context cache overflow beyond VRAM.
- **`--n-cpu-moe`**: Offloads a specified count of MoE expert layers to CPU/RAM to fit massive models.

</sub>

---

### Hardware Profiles Reference

| Parameter | Balanced (Default) | Max Quality | Max Performance |
| :--- | :--- | :--- | :--- |
| **Target Use Case** | <sub>General reasoning, coding, chat</sub> | <sub>Lossless recall, critical accuracy</sub> | <sub>Ultra-fast token generation</sub> |
| **GPU Layers (`-ngl`)** | <sub>99 (All)</sub> | <sub>99 (All)</sub> | <sub>99 (All)</sub> |
| **Context Size (`-c`)** | <sub>65,536 (64K)</sub> | <sub>131,072 (128K)</sub> | <sub>32,768 (32K)</sub> |
| **Batch Size (`-b`)** | <sub>1024</sub> | <sub>1024</sub> | <sub>2048</sub> |
| **Micro-Batch (`-ub`)** | <sub>256</sub> | <sub>256</sub> | <sub>512</sub> |
| **KV Cache K / V** | <sub>q8_0 / q8_0</sub> | <sub>f16 / f16</sub> | <sub>q4_0 / q4_0</sub> |
| **Temperature / Top-P** | <sub>0.5 / 0.95</sub> | <sub>0.7 / 0.95</sub> | <sub>0.5 / 0.90</sub> |
| **Flash Attention (`-fa`)** | <sub>Enabled</sub> | <sub>Enabled</sub> | <sub>Enabled</sub> |
| **Jinja Templates (`--jinja`)** | <sub>Enabled</sub> | <sub>Enabled</sub> | <sub>Enabled</sub> |
| **Memory Lock (`--load-mode`)** | <sub>Off</sub> | <sub>Enabled (`mlock`)</sub> | <sub>Enabled (`mlock`)</sub> |
| **Prompt Threads (`-tb`)** | <sub>Off</sub> | <sub>Off</sub> | <sub>Enabled (`8`)</sub> |
| **VRAM Headroom (`--fit-target`)**| <sub>Off</sub> | <sub>Enabled (`1024 MiB`)</sub> | <sub>Enabled (`1024 MiB`)</sub> |
| **Dedicated Slot (`-np`)** | <sub>Off</sub> | <sub>Off</sub> | <sub>Enabled (`1`)</sub> |
| **KV Cache Reuse** | <sub>Off</sub> | <sub>Enabled (`256`)</sub> | <sub>Enabled (`256`)</sub> |

---

### Quickstart (No Python Required)

<sub>

1. **Download LLauncher**: Download `LLauncher.exe` from [Releases](https://github.com/artifyr/LLauncher/releases) (or grab `dist/LLauncher.exe`). **No installation required**—it runs immediately out of the box.
2. **Download llama.cpp (`llama-server.exe`)**: Grab pre-built Windows binaries matching your GPU (`vulkan`, `cuda`, or `cpu`) from [llama.cpp Releases](https://github.com/ggml-org/llama.cpp/releases) and extract them (or use the in-app **🔄 Update** button).
3. **Download a GGUF Model**: Download any `.gguf` quantized model (or use the built-in **⬇ HF Models** downloader).
4. **Launch**: Open `LLauncher.exe`, select your `llama-server.exe` and model file, then click **Start Model Server**.

</sub>

---

### Running from Source & Building

```bash
# Clone & run from source
git clone https://github.com/artifyr/LLauncher.git
cd LLauncher
pip install customtkinter pywinstyles pystray pillow
python launcher.py

# Build standalone executable
pyinstaller --clean Llauncher.spec
```

<sub>The resulting executable is generated at `dist/LLauncher.exe`.</sub>

---

### Hardware Profiles (Manual Import)

<sub>LLauncher includes pre-configured profile scripts located in `profiles/`, split into `general/` (dense models with MoE off) and `MoE/` (MoE-specific models with `--n-cpu-moe 16`). These can be imported via **Import .ps1** in the footer or run directly in PowerShell.</sub>

#### General Profiles (`profiles/general/`)
| Profile Script | Target Hardware | Recommended Context (`-c`) | Batch (`-b` / `-ub`) | Cache Type | Key Optimizations |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `profile_4gb_vram.ps1` | <sub>4 GB VRAM (GTX 1650, RTX 3050 mobile)</sub> | <sub>8,192 tokens</sub> | <sub>512 / 128</sub> | <sub>`q4_0`</sub> | <sub>Memory conservative, `--fit-target 256`</sub> |
| `profile_8gb_vram.ps1` | <sub>8 GB VRAM (RTX 3070, 4060, RX 6600)</sub> | <sub>16,384 tokens</sub> | <sub>512 / 256</sub> | <sub>`q4_0`</sub> | <sub>`-ngl 99`, `--fit-target 512`</sub> |
| `profile_12gb_vram.ps1` | <sub>12 GB VRAM (RTX 3060 12GB, 4070, RX 6700 XT)</sub> | <sub>32,768 tokens</sub> | <sub>1024 / 256</sub> | <sub>`q8_0`</sub> | <sub>High throughput, `q8_0` KV, `--fit-target 768`</sub> |
| `profile_16gb_vram.ps1` | <sub>16 GB VRAM (RTX 4080, RX 7800 XT, 9070 XT)</sub> | <sub>65,536 tokens</sub> | <sub>1024 / 256</sub> | <sub>`q8_0`</sub> | <sub>Extended context, high batch throughput</sub> |
| `profile_24gb_vram.ps1` | <sub>24 GB+ VRAM (RTX 3090, RTX 4090, Workstations)</sub> | <sub>131,072 tokens</sub> | <sub>2048 / 512</sub> | <sub>`q8_0`</sub> | <sub>Maximum context, `mlock`, RAM cache reservation</sub> |

#### MoE Profiles (`profiles/MoE/`)
| Profile Script | Target Hardware | Recommended Context (`-c`) | Batch (`-b` / `-ub`) | Cache Type | Key Optimizations |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `profile_12gb_vram.ps1` | <sub>12 GB VRAM (RTX 3060 12GB, 4070, RX 6700 XT)</sub> | <sub>16,384 tokens</sub> | <sub>512 / 128</sub> | <sub>`q4_0`</sub> | <sub>Hybrid offload (`-ngl 28`), `--n-cpu-moe 16`, 8GB RAM cache</sub> |
| `profile_16gb_vram.ps1` | <sub>16 GB VRAM (RTX 4080, RX 7800 XT, 9070 XT)</sub> | <sub>32,768 tokens</sub> | <sub>1024 / 256</sub> | <sub>`q8_0`</sub> | <sub>Accelerated offload (`-ngl 33`), `--n-cpu-moe 16`, `-tb 8`</sub> |
| `profile_24gb_vram.ps1` | <sub>24 GB VRAM (RTX 3090, RTX 4090, RX 7900 XTX)</sub> | <sub>32,768 tokens</sub> | <sub>1024 / 256</sub> | <sub>`q8_0`</sub> | <sub>Full offload (`-ngl 99`), `mlock`, 16GB RAM cache, `--n-cpu-moe 16`</sub> |
| `profile_32gb_vram.ps1` | <sub>32 GB+ VRAM (RTX 5090, RTX 6000 Ada, Multi-GPU)</sub> | <sub>65,536 tokens</sub> | <sub>2048 / 512</sub> | <sub>`q8_0`</sub> | <sub>64K context, 2048 batch, `mlock`, `--fit-target 1536`, `--n-cpu-moe 16`</sub> |

---

### File Structure

```
LLauncher/
|-- assets/
|   |-- Logo.png           # Header brand logo
|   \-- llauncher.ico      # Application and tray icon
|-- dist/
|   \-- LLauncher.exe      # Compiled standalone Windows executable
|-- profiles/              # Hardware preset scripts (manual import)
|   |-- general/           # Dense LLM profiles (MoE disabled)
|   \-- MoE/               # Mixture-of-Experts profiles (--n-cpu-moe 16)
|-- launcher.py            # Main application source code
|-- Llauncher.spec         # PyInstaller build specification
|-- profiles.json          # Persistent profiles configuration
|-- recent_models.json     # Persistent recent models history
|-- README.md              # Project documentation
\-- .gitignore             # Git ignore rules
```

---

### License

<sub>This project is open-source under the [GNU General Public License v3.0 (GPL-3.0)](LICENSE).</sub>
