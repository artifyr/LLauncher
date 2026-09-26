# =====================================================================
# LLauncher MoE Profile: 24GB VRAM (High-Throughput MoE Architecture)
# Target Hardware: GPUs with 24GB VRAM (e.g. RTX 3090, RTX 4090, RX 7900 XTX)
# Target Models: Mixtral 8x7B (Full offload Q4/Q5), Mixtral 8x22B (Partial), Qwen 2.5 72B MoE
# Strategy: Near-full GPU layer offloading (ngl 45-99) with selective CPU MoE offload fallback
# =====================================================================

$env:GGML_VK_DISABLE_PINNED = '1'

$llamaExe = "llama-server.exe"

$serverArgs = @(
    "--device", "Vulkan0",
    "-ngl", "99",
    "-c", "32768",
    "-t", "8",
    "-b", "1024",
    "-ub", "256",
    "-ctk", "q8_0",
    "-ctv", "q8_0",
    "--host", "127.0.0.1",
    "--port", "8082",
    "--temp", "0.5",
    "--top-p", "0.95",
    "--min-p", "0.05",
    "-fa", "on",
    "--jinja",
    "--load-mode", "mlock",
    "-tb", "8",
    "--fit-target", "1024",
    "--cache-reuse", "256",
    "--cache-ram", "16384",
    "--n-cpu-moe", "16"
)

Write-Host "Launching llama-server with 24GB MoE Profile..." -ForegroundColor Cyan
& $llamaExe @serverArgs

# =====================================================================
# LLauncher Embedded Settings (For importing back into LLauncher)
# <LLAUNCHER_SETTINGS_JSON>
# {
#   "version": "1.3.0",
#   "profile_name": "24GB VRAM MoE Optimized",
#   "device": "Vulkan0",
#   "ngl": 99,
#   "ctx_index": 5,
#   "ctx_tokens": 32768,
#   "batch_index": 3,
#   "batch_size": 1024,
#   "ubatch_index": 1,
#   "ubatch_size": 256,
#   "threads": "8",
#   "port": "8082",
#   "ctk": "q8_0",
#   "ctv": "q8_0",
#   "temp": "0.5",
#   "topp": "0.95",
#   "minp": "0.05",
#   "flash_attention": true,
#   "jinja": true,
#   "optimizations": {
#     "mlock": {
#       "enabled": true,
#       "value": "mlock"
#     },
#     "tb": {
#       "enabled": true,
#       "value": "8"
#     },
#     "fit_target": {
#       "enabled": true,
#       "value": "1024"
#     },
#     "cache_reuse": {
#       "enabled": true,
#       "value": "256"
#     },
#     "parallel": {
#       "enabled": false,
#       "value": "1"
#     },
#     "cache_ram": {
#       "enabled": true,
#       "value": "16384"
#     },
#     "cpu_moe": {
#       "enabled": true,
#       "value": "16"
#     }
#   }
# }
# </LLAUNCHER_SETTINGS_JSON>
# =====================================================================
