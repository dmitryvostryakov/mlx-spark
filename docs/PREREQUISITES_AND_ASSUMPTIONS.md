# Предпосылки: AVAILABLE / DERIVABLE / MISSING

| Предпосылка | Статус | Действие |
|---|---|---|
| Цель full independent MLX-like | AVAILABLE: явно зафиксирована владельцем | Не уточнять заново |
| Single Spark first, TP2 later | AVAILABLE: явно зафиксировано владельцем | Scope protected |
| Два Spark с QSFP/ConnectX-7 | AVAILABLE: сведения владельца | Второй узел сейчас не нужен |
| Первая модель Qwen3.8-27B | AVAILABLE | Model audit по источникам |
| Публичный config/source anatomy | AVAILABLE как web observation | Immutable download+compare before runtime |
| Memory arithmetic по config | DERIVABLE | CLI даёт estimate, не fit verdict |
| Full HF revision | MISSING | Metadata resolver, review; не fake pin |
| Actual DGX OS/CUDA/driver/cuDNN/compiler | MISSING | Harmless local inventory на выбранном Spark |
| Actual disk/memory/workloads | MISSING | Budget before load/convert/build |
| GPU execution results | MISSING | Реальные isolated hardware tests; CPU не заменяет |
| Exact public API parity baseline | DERIVABLE после source import | FND-07, seed list не полный |
| Performance target/quality tolerance | MISSING до baseline | Зафиксировать до candidate acceptance |
| Public license/package-name release decision | MISSING | Решение владельца перед публикацией |

Отсутствие target hardware facts не мешает подготовить данный hand-off и развивать CPU/reference contracts.
Оно блокирует только конкретное заявление о target build, model correctness, memory fit и performance.
