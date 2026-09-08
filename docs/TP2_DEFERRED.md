# TP=2 — зафиксировано, но сейчас не реализуется

**Статус: DEFERRED BY OWNER.** Два Spark и QSFP/ConnectX-7 доступны по словам владельца.
Первая фаза обязана быть закончена на одном узле без network/distributed requirements.

## Условие открытия

Stable single-Spark release, полный evidence gate и явный переход к следующей фазе.
Не text-only alpha, не успешный CUDA toy, не passing CPU CI. Пока не выполнено — no NCCL setup,
no network inventory, no SSH to second Spark, no distributed scheduler/allocator/launcher.

## Что сохранить в архитектуре сейчас

Generic primitive semantics, explicit shape axes, model-independent kernels, versioned checkpoint,
separation of model layout и physical execution. Не надо заранее писать DistributedTensor/world_size/communicator abstractions.
Обычная чистая модульность достаточна; это не разрешение на hidden phase2 work.

## Что потребуется после unlock

Проверить фактическую link speed/latency/topology, transport support и host-buffer constraints.
Spark network не даёт общей когерентной 256GB UMA. NVIDIA отдельно описывает GPUDirect ограничения [S06].
Выбрать actual NCCL/transport path после measurement, не скопировать H100 assumptions.

Для модели отдельно проверить tensor partition embeddings/FFN/attention и packed GDN projections,
сохранить Hv/Hk grouping/state ownership и replication correctness. Пока это задачи TP2-03+, не код первой фазы.
Qwen TP=2 не означает pipeline/expert parallel или arbitrary cluster. Performance сравнивать с TP1 at same precision/context.

## Что не менять

Single-Spark package default не должен требовать сети или distributed extra после расширения.
TP1 остаётся самостоятельным поддерживаемым mode с собственным regression suite.
Не обещать 2x ускорение; малая latency задача может проиграть межузловым коммуникациям.
