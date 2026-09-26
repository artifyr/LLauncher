# =====================================================================
# LLauncher Profile: 4GB VRAM (Entry Level & Compact Models)
# Target Hardware: GPUs with 4GB VRAM (e.g. GTX 1650, RX 6500 XT, laptop GPUs)
# Suggested Models: 1B to 4B parameters (Q4_K_M / Q4_0), partial offload for 7B/8B
# Note: MoE CPU offloading is disabled for universal compatibility.
# =====================================================================

$env:GGML_VK_DISABLE_PINNED = '1'

$llamaExe = "llama-server.exe"

$serverArgs = @(
    "--device", "Vulkan0",
    "-ngl", "33",
    "-c", "8192",
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
    "--fit-target", "256",
    "--cache-reuse", "128"
)

Write-Host "Launching llama-server with 4GB VRAM Profile..." -ForegroundColor Cyan
& $llamaExe @serverArgs

# =====================================================================
# LLauncher Embedded Settings (For importing back into LLauncher)
# <LLAUNCHER_SETTINGS_JSON>
# {
#   "version": "1.3.0",
#   "profile_name": "4GB VRAM Universal",
#   "device": "Vulkan0",
#   "ngl": 33,
#   "ctx_index": 2,
#   "ctx_tokens": 8192,
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
#       "value": "256"
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
