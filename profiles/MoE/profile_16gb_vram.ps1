# =====================================================================
# LLauncher MoE Profile: 16GB VRAM (Accelerated MoE Offload)
# Target Hardware: GPUs with 16GB VRAM (e.g. RX 6800/7800 XT/9070 XT, RTX 4080)
# Target Models: Mixtral 8x7B (Q4_K_M), Qwen 2.5 32B MoE, DBRX
# Strategy: Offload majority of layers (ngl 33) to GPU, offload 16 expert layers to CPU
# =====================================================================

$env:GGML_VK_DISABLE_PINNED = '1'

$llamaExe = "llama-server.exe"

$serverArgs = @(
    "--device", "Vulkan0",
    "-ngl", "33",
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
    "-tb", "8",
    "--fit-target", "768",
    "--cache-reuse", "256",
    "--cache-ram", "8192",
    "--n-cpu-moe", "16"
)

Write-Host "Launching llama-server with 16GB MoE Profile..." -ForegroundColor Cyan
& $llamaExe @serverArgs

# =====================================================================
# LLauncher Embedded Settings (For importing back into LLauncher)
# <LLAUNCHER_SETTINGS_JSON>
# {
#   "version": "1.3.0",
#   "profile_name": "16GB VRAM MoE Optimized",
#   "device": "Vulkan0",
#   "ngl": 33,
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
#       "enabled": false,
#       "value": "mlock"
#     },
#     "tb": {
#       "enabled": true,
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
