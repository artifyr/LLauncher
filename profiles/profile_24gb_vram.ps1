# =====================================================================
# LLauncher Profile: 24GB VRAM and Higher (Enthusiast & Workstation GPUs)
# Target Hardware: GPUs with 24GB+ VRAM (e.g. RTX 3090/4090, RX 7900 XTX)
# Suggested Models: 32B to 70B parameters (Q4_K_M) or 14B models with 128K context
# Note: MoE CPU offloading is disabled for universal compatibility.
# =====================================================================

$env:GGML_VK_DISABLE_PINNED = '1'

$llamaExe = "llama-server.exe"

$serverArgs = @(
    "--device", "Vulkan0",
    "-ngl", "99",
    "-c", "131072",
    "-t", "8",
    "-b", "2048",
    "-ub", "512",
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
    "--fit-target", "1536",
    "--cache-reuse", "256",
    "--cache-ram", "16384"
)

Write-Host "Launching llama-server with 24GB+ VRAM Profile..." -ForegroundColor Cyan
& $llamaExe @serverArgs

# =====================================================================
# LLauncher Embedded Settings (For importing back into LLauncher)
# <LLAUNCHER_SETTINGS_JSON>
# {
#   "version": "1.3.0",
#   "profile_name": "24GB+ VRAM Universal",
#   "device": "Vulkan0",
#   "ngl": 99,
#   "ctx_index": 9,
#   "ctx_tokens": 131072,
#   "batch_index": 4,
#   "batch_size": 2048,
#   "ubatch_index": 2,
#   "ubatch_size": 512,
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
#       "enabled": false,
#       "value": "8"
#     },
#     "fit_target": {
#       "enabled": true,
#       "value": "1536"
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
#       "enabled": false,
#       "value": "16"
#     }
#   }
# }
# </LLAUNCHER_SETTINGS_JSON>
# =====================================================================
