# =====================================================================
# LLauncher Profile: 8GB VRAM (Mainstream Gaming & Productivity GPUs)
# Target Hardware: GPUs with 8GB VRAM (e.g. RTX 3060/3070/4060, RX 6600/7600)
# Suggested Models: 7B to 9B parameters (Q4_K_M / Q5_K_M), full offload
# Note: MoE CPU offloading is disabled for universal compatibility.
# =====================================================================

$env:GGML_VK_DISABLE_PINNED = '1'

$llamaExe = "llama-server.exe"

$serverArgs = @(
    "--device", "Vulkan0",
    "-ngl", "99",
    "-c", "16384",
    "-t", "8",
    "-b", "512",
    "-ub", "256",
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
    "--cache-reuse", "256"
)

Write-Host "Launching llama-server with 8GB VRAM Profile..." -ForegroundColor Cyan
& $llamaExe @serverArgs

# =====================================================================
# LLauncher Embedded Settings (For importing back into LLauncher)
# <LLAUNCHER_SETTINGS_JSON>
# {
#   "version": "1.3.0",
#   "profile_name": "8GB VRAM Universal",
#   "device": "Vulkan0",
#   "ngl": 99,
#   "ctx_index": 3,
#   "ctx_tokens": 16384,
#   "batch_index": 2,
#   "batch_size": 512,
#   "ubatch_index": 1,
#   "ubatch_size": 256,
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
#       "value": "256"
#     },
#     "parallel": {
#       "enabled": false,
#       "value": "1"
#     },
#     "cache_ram": {
#       "enabled": false,
#       "value": "4096"
#     },
#     "cpu_moe": {
#       "enabled": false,
#       "value": "16"
#     }
#   }
# }
# </LLAUNCHER_SETTINGS_JSON>
# =====================================================================
