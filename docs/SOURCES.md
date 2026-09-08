# Первичные источники и доверие

Проверка публичных источников: **2026-09-08**. Никакие факты о текущем состоянии приватных Spark не получены из этих страниц.

## S01 — Qwen3.8-27B configuration

https://huggingface.co/Qwen/Qwen3.8-27B/resolve/1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0/config.json

Использование/ограничение: architecture and shape facts at exact revision; raw SHA-256
`191e0af232104ed8b65258cf3fb2b842e288008baca7633c11b82a1ac7203aab`; local normalized fixture is
structurally equal but retains its own byte hash.

## S02 — Qwen3.8-27B official model card

https://huggingface.co/Qwen/Qwen3.8-27B/tree/1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0

Использование/ограничение: model identity/multimodal description/license indication; no own performance validation.

## S03 — MLX official repository

https://github.com/ml-explore/mlx

Использование/ограничение: API families, CUDA presence, project scope.

## S04 — MLX candidate immutable commit

https://github.com/ml-explore/mlx/commit/365bd0fbac2e96631a1b2c4a34ca5a0771cdfde5

Использование/ограничение: full SHA observed; starting-source candidate, not hardware-certified build.

## S05 — NVIDIA DGX Spark hardware guide

https://docs.nvidia.com/dgx/dgx-spark/hardware.html

Использование/ограничение: memory/platform facts; actual local system still must be inventoried.

## S06 — NVIDIA DGX Spark CUDA porting guide

https://docs.nvidia.com/dgx/dgx-spark-porting-guide/porting/cuda.html

Использование/ограничение: allocation access/GPUDirect caveats; TP2 deferred.

## S07 — NVIDIA compute capability table

https://developer.nvidia.com/cuda/gpus

Использование/ограничение: GB10 compute capability12.1; probe local hardware as well.

## S08 — MLX official install/API documentation

https://ml-explore.github.io/mlx/build/html/install.html

Использование/ограничение: installation docs/API surface; docs version and main source may differ.

## S09 — MLX published LICENSE

https://raw.githubusercontent.com/ml-explore/mlx/365bd0fbac2e96631a1b2c4a34ca5a0771cdfde5/LICENSE

Использование/ограничение: exact-revision MIT notice, SHA-256
`ccfab7ccb2ea306f71531c8ca77bb55507606cd90768b1e32b8b52ab5b48cf01`; preserve it upon source import.

## S10 — MLX-LM Gated Delta implementation

https://raw.githubusercontent.com/ml-explore/mlx-lm/7fb4be44d560e5b74595210f83cb6003a57e52a7/mlx_lm/models/gated_delta.py

Использование/ограничение: exact-revision source-level recurrence/mask/scale reference; not a runtime dependency.

## S11 — MLX-LM Qwen3.5-family model source

https://raw.githubusercontent.com/ml-explore/mlx-lm/7fb4be44d560e5b74595210f83cb6003a57e52a7/mlx_lm/models/qwen3_5.py

Использование/ограничение: reference for source audit; not proof of complete Qwen3.8 compatibility.

## S12 — MLX official function transforms documentation

https://ml-explore.github.io/mlx/build/html/usage/function_transforms.html

Использование/ограничение: compositional transform design; must verify against pinned release.

## S13 — MLX pinned CMakeLists

https://raw.githubusercontent.com/ml-explore/mlx/365bd0fbac2e96631a1b2c4a34ca5a0771cdfde5/CMakeLists.txt

Использование/ограничение: exact source constraints; CUDA 13.1 is rejected. This is not a successful build or
DGX2 compatibility result. The file hash is retained in `configs/source-lock.resolved.json`.

## S14 — MLX CUDA CMakeLists

https://raw.githubusercontent.com/ml-explore/mlx/365bd0fbac2e96631a1b2c4a34ca5a0771cdfde5/mlx/backend/cuda/CMakeLists.txt

Использование/ограничение: exact backend constraints and dependency declarations; not a guarantee for SM 12.1
or any dtype. Several upstream FetchContent declarations are tag/archive based; FND-03 resolves their source
commits, but networked build remains denied until FND-04 materializes or overrides those exact revisions.

## S15 — Qwen exact model commit

https://huggingface.co/Qwen/Qwen3.8-27B/commit/1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0

Использование/ограничение: exact immutable model revision resolved and metadata-audited; this is not model-runtime
validation and does not imply that weight shard bytes were re-hashed.

## Что считать доказательством

Документированный hardware capability, наблюдение source и наш runtime measurement — разные уровни.
Ссылки main динамические; production использует full reviewed lock. Не копировать claims из старых ответов без проверки.
Никакие числа speedup, model quality или target-toolchain success в этом hand-off не выдаются как измеренные на Spark.
Первичные файлы config — фактические данные; нормализованная запись снабжена явным происхождением.

## S16 — CUDA runtime device properties

https://docs.nvidia.com/cuda/cuda-runtime-api/structcudaDeviceProp.html

Поля capability probe сверены с API; сам probe не компилировался/не запускался на GPU в этой среде.
