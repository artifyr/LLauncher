# =====================================================================
# LLauncher MoE Profile: 12GB VRAM (Hybrid GPU/CPU MoE Offload)
# Target Hardware: GPUs with 12GB VRAM (e.g. RTX 3060 12GB, RTX 4070, RX 6700 XT)
# Target Models: Mixtral 8x7B (Q3_K_M / Q4_K_M), Qwen 2.5 14B/32B MoE, DeepSeek-Lite MoE
# Strategy: Offload attention & core layers to GPU, route 16 MoE expert layers to CPU
# =====================================================================

$env:GGML_VK_DISABLE_PINNED = '1'

$llamaExe = "llama-server.exe"

$serverArgs = @(
    "--device", "Vulkan0",
    "-ngl", "28",
    "-c", "16384",
    "-t", "8",
    "-b", "512",
    "-ub", "128",
    "-ctk", "q4_0",
    "-ctv", "q4_0",
    "--host", "127.0.0.1",
    "--port", "8082",
    "--temp", "0.6",
    "--top-p", "0.95",
    "--min-p", "0.05",
    "-fa", "on",
    "--jinja",
    "--fit-target", "512",
    "--cache-reuse", "128",
    "--cache-ram", "8192",
    "--n-cpu-moe", "16"
)

Write-Host "Launching llama-server with 12GB MoE Profile..." -ForegroundColor Cyan
& $llamaExe @serverArgs

# =====================================================================
# LLauncher Embedded Settings (For importing back into LLauncher)
# <LLAUNCHER_SETTINGS_JSON>
# {
#   "version": "1.3.0",
#   "profile_name": "12GB VRAM MoE Optimized",
#   "device": "Vulkan0",
#   "ngl": 28,
#   "ctx_index": 3,
#   "ctx_tokens": 16384,
#   "batch_index": 2,
#   "batch_size": 512,
#   "ubatch_index": 0,
#   "ubatch_size": 128,
#   "threads": "8",
#   "port": "8082",
#   "ctk": "q4_0",
#   "ctv": "q4_0",
#   "temp": "0.6",
#   "topp": "0.95",
#   "minp": "0.05",
#   "flash_attention": true,
#   "jinja": true,
#   "optimizations": {
#     "mlock": {
#       "enabled": false,
#       "value": "mlock"
#     },
#     "tb": {
#       "enabled": false,
#       "value": "8"
#     },
#     "fit_target": {
#       "enabled": true,
#       "value": "512"
#     },
#     "cache_reuse": {
#       "enabled": true,
#       "value": "128"
#     },
#     "parallel": {
#       "enabled": false,
#       "value": "1"
#     },
#     "cache_ram": {
#       "enabled": true,
#       "value": "8192"
#     },
#     "cpu_moe": {
#       "enabled": true,
#       "value": "16"
#     }
#   }
# }
# </LLAUNCHER_SETTINGS_JSON>
# =====================================================================
