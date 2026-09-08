# Риски и неизвестные

| Риск | Ранний признак | Защита / решение |
|---|---|---|
| Проект снова становится Qwen launcher | Только generate CLI, нет autodiff/module tests | API parity и generic training release gates |
| Независимость только номинальная | Runtime импортирует installed mlx/torch | Clean env dependency/import audit |
| UMA предположения неверны | Host reads device pointer, OOM accounting противоречив | Capability tests и отдельные allocation contracts |
| Kernel быстрый, модель неверна | Короткие tests проходят, long recurrence drift | Layerwise + state + gradient + long context checks |
| Autograd незаметно сломан | Loss выглядит правдоподобно, adapters не учатся | Finite differences, input gradients, freeze/hash tests |
| Compile превращён в no-op | Функция работает, нет graph evidence | Semantic+execution proof, no identity stubs |
| Upstream/main дрейфует | Новый config/toolkit ломает build | Immutable locks и reviewed upgrades |
| «4-bit модель» почти не помещается | Большие unquantized tensors/workspaces | Exact tensor and peak accounting |
| Namespace fork ломает interop | Capsule/type/serialization mismatch | Separate binding/ABI migration tasks |
| MTP rollback неверен | Ошибки после rejected draft | All-state reject-position fixtures |
| Host перегружен | Concurrent benchmarks/OOM | Single-owner resource lock, staged budgets |
| Агент теряет ограничения | Ранний NCCL/HTTP/Flash-Next | AGENTS+CONTEXT+scope gates |
| Поддельный green | Skips/templates засчитаны как evidence | Fail-closed checker и independent review |
| Неподтверждённые обещания скорости | Числа из чужих issues | Raw measured evidence only |

## Неизвестные до target discovery

Actual OS/driver/toolkit/cuDNN/host compiler; compatibility ARM64 dependency wheels;
exact immutable HF revision; полный список tensors/parameter bytes; actual free memory/disk;
новый public package name/license; точные model numerical thresholds и realistic performance baseline.
Это фиксируемые входные данные задач, не разрешение на догадки и не причина отказаться от плана.

## Что требует решения владельца позднее

Системные изменения, внешняя публикация/бренд/лицензия, расширение scope, private data use и фактический старт TP2.
Большинство инженерных решений внутри approved single-Spark scope принимается через ADR/review без повторных
вопросов о цели, модели и аппаратном порядке.
