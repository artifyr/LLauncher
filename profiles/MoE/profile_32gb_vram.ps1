# =====================================================================
# LLauncher MoE Profile: 32GB VRAM and Above (Flagship & Multi-GPU MoE)
# Target Hardware: GPUs with 32GB+ VRAM (e.g. RTX 5090, RTX 6000 Ada, Dual RTX 3090/4090)
# Target Models: Mixtral 8x22B, Command-R+, DeepSeek-V2/V3 MoE, Qwen MoE
# Strategy: Maximum GPU offloading, expanded 64K+ context, RAM pin lock, 16 MoE expert workers
# =====================================================================

$env:GGML_VK_DISABLE_PINNED = '1'

$llamaExe = "llama-server.exe"

$serverArgs = @(
    "--device", "Vulkan0",
    "-ngl", "99",
    "-c", "65536",
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
    "-tb", "8",
    "--fit-target", "1536",
    "--cache-reuse", "256",
    "--cache-ram", "16384",
    "--n-cpu-moe", "16"
)

Write-Host "Launching llama-server with 32GB+ MoE Profile..." -ForegroundColor Cyan
& $llamaExe @serverArgs

# =====================================================================
# LLauncher Embedded Settings (For importing back into LLauncher)
# <LLAUNCHER_SETTINGS_JSON>
# {
#   "version": "1.3.0",
#   "profile_name": "32GB+ VRAM MoE Optimized",
#   "device": "Vulkan0",
#   "ngl": 99,
#   "ctx_index": 7,
#   "ctx_tokens": 65536,
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
#       "enabled": true,
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
#       "enabled": true,
#       "value": "16"
#     }
#   }
# }
# </LLAUNCHER_SETTINGS_JSON>
# =====================================================================
