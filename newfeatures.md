# LLauncher - Feature Roadmap & Enhancement Proposals

This document outlines planned and proposed features for **LLauncher** to expand its capabilities as a high-performance local LLM server orchestration tool.

---

## 1. Hardware & VRAM Telemetry
- **Live VRAM & System RAM Meters**: Real-time visualization of dedicated GPU VRAM and host RAM usage (via DXGI/Vulkan and `psutil`) to monitor memory consumption dynamically.
- **Pre-Launch Fit & OOM Estimator**: Calculate projected VRAM footprint based on model parameter count, quantization format, selected context window (`-c`), and KV cache quant (`-ctk`/`-ctv`) before launching to warn against Out-Of-Memory failures.
- **Real-Time Token & Slot Metrics**: Ticker or subtle progress display polling `llama-server`'s `/health` and `/metrics` endpoints to show active generation speed (tokens/sec), prompt evaluation speed, and slot saturation.
- **Multi-GPU / Split-Mode Management**: Dedicated controls for multi-GPU setups (`-ts` / `--tensor-split`), device selection per layer, and unified memory configuration.

---

## 2. Model & Library Management
- **Recent Models & Quick Favorites**: History dropdown storing recently used `.gguf` files for fast switching without file dialogs.
- **Auto-Detect Vision Projector (`mmproj`)**: Automatic detection of matching multimodal projector files (`mmproj-*.gguf`) in the same directory when a vision-enabled model (e.g. Qwen2-VL, LLaVA, MiniCPM) is selected.
- **Native GGUF Header Inspector**: Instant inspection of selected GGUF files to display model architecture, parameter count, default context length, and tensor quantization directly in the UI.
- **Hugging Face Hub Downloader / Browser**: Integrated search and download tool for GGUF model repositories with direct progress indicators and automatic placement into the user's model library.

---

## 3. Server Networking & Security
- **Network Host Mode Switch**: Quick toggle between `Local Only (127.0.0.1)` and `LAN / Network Exposed (0.0.0.0)` for serving local clients.
- **API Key Authentication (`--api-key`)**: Optional field to protect the OpenAI-compatible `/v1` endpoint when accessible over the network.
- **CORS & SSL Configuration**: One-click configuration for CORS origins (to support browser clients like Open WebUI without proxies) and custom SSL certificates.

---

## 4. Frontend & Client Integrations
- **"Open Web UI" Quick Launcher**: One-click button to open `http://127.0.0.1:<port>` in the default browser when the server is online.
- **One-Click Client Configurations**: Pre-formatted snippets and auto-configuration files for popular frontends:
  - Open WebUI
  - SillyTavern
  - Continue / Cline (VS Code / JetBrains)
  - Jan / LM Studio / LibreChat
- **API Endpoint Tester / Health Check**: Built-in ping tool to test `/v1/models` and `/v1/chat/completions` directly inside the launcher to verify server responsiveness.

---

## 5. Advanced Inference Optimizations
- **LoRA Adapter Stacking**: Dynamic interface for attaching one or more `--lora` adapter files along with custom scaling weights (`--lora-scaled`).
- **Speculative Decoding (`--model-draft`)**: Support for configuring a smaller draft model alongside the main model to boost inference throughput on capable hardware.
- **Continuous Batching & Context Shift**: Toggles for `--cont-batching`, `--ctx-shift` (preventing server halts when context maxes out), and `--defrag-thold`.
- **Grammar & Structured Output Presets**: Option to provide default JSON schemas or BNF grammars (`--grammar`) for structured data extraction workflows.

---

## 6. Process Management & Desktop Ergonomics
- **System Tray Integration**: Minimize launcher to the Windows notification tray with a right-click menu (`Start`, `Stop`, `Restart`, `View Logs`, `Exit`).
- **Collapsible Embedded Log Console**: Optional in-window terminal drawer displaying real-time `llama-server` stdout/stderr with search and filter capabilities, reducing reliance on external console windows.
- **Auto-Restart on Crash**: Background watchdog that monitors server health and automatically restarts the engine if an unexpected process termination occurs.
- **Export CLI Script / PowerShell Launcher**: "Export as Script" feature that saves the generated parameters as a standalone `.ps1` or `.bat` file for headless servers or background automation.
