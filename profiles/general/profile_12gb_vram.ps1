# =====================================================================
# LLauncher Profile: 12GB VRAM (Upper-Midrange GPUs)
# Target Hardware: GPUs with 12GB VRAM (e.g. RTX 3060 12GB, RTX 4070, RX 6700 XT)
# Suggested Models: 7B to 14B parameters (Q4_K_M / Q8_0), extended context
# Note: MoE CPU offloading is disabled for universal compatibility.
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
    "--temp", "0.6",
    "--top-p", "0.95",
    "--min-p", "0.05",
    "-fa", "on",
    "--jinja",
    "--fit-target", "768",
    "--cache-reuse", "256"
)

Write-Host "Launching llama-server with 12GB VRAM Profile..." -ForegroundColor Cyan
& $llamaExe @serverArgs

# =====================================================================
# LLauncher Embedded Settings (For importing back into LLauncher)
# <LLAUNCHER_SETTINGS_JSON>
# {
#   "version": "1.3.0",
#   "profile_name": "12GB VRAM Universal",
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
#       "value": "768"
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
#       "enabled": false,
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
