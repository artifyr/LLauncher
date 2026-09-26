# =====================================================================
# LLauncher Profile: 16GB VRAM (High-End GPUs)
# Target Hardware: GPUs with 16GB VRAM (e.g. RX 6800/7800 XT/9070 XT, RTX 4080)
# Suggested Models: 14B to 32B parameters (Q4_K_M) or 8B models with 64K+ context
# Note: MoE CPU offloading is disabled for universal compatibility.
# =====================================================================

$env:GGML_VK_DISABLE_PINNED = '1'

$llamaExe = "llama-server.exe"

$serverArgs = @(
    "--device", "Vulkan0",
    "-ngl", "99",
    "-c", "65536",
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
    "--fit-target", "1024",
    "--cache-reuse", "256"
)

Write-Host "Launching llama-server with 16GB VRAM Profile..." -ForegroundColor Cyan
& $llamaExe @serverArgs

# =====================================================================
# LLauncher Embedded Settings (For importing back into LLauncher)
# <LLAUNCHER_SETTINGS_JSON>
# {
#   "version": "1.3.0",
#   "profile_name": "16GB VRAM Universal",
#   "device": "Vulkan0",
#   "ngl": 99,
#   "ctx_index": 7,
#   "ctx_tokens": 65536,
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
#       "enabled": false,
#       "value": "mlock"
#     },
#     "tb": {
#       "enabled": false,
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
#       "value": "8192"
#     },
#     "cpu_moe": {
#       "enabled": false,
#       "value": "16"
#     }
#   }
# }
# </LLAUNCHER_SETTINGS_JSON>
# =====================================================================
