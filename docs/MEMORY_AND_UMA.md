# Память, UMA и ограниченные бюджеты

## Физическая и программная модель

У Spark 128 GB CPU/GPU shared memory, заявленная bandwidth 273 GB/s [S05]. Это не значит, что каждый CUDA pointer
можно безопасно читать CPU или NIC. NVIDIA описывает ограничения device allocations и необходимость capability query [S06].
Не считать cudaMemGetInfo/nvidia-smi единственным источником available memory; учитывать ОС/cgroups и реальный allocation behavior.
Память CPU и GPU не складывается в 256GB на одном узле. Offload в тот же pool не увеличивает физическую ёмкость.

## Accounting

Разделить: source weights, converted weights, adapter weights, gradients, optimizer states, activation checkpointing,
attention KV, recurrent GDN, conv history, vision temporary, MTP draft/verify, output logits,
CUDA/library workspaces, allocator cached/pending, file mapping/page cache, system reserve.
Peak during load/convert/train важнее только steady-state resident size. Avoid all-weights deserialization twice.

## Проверяемая арифметика config

Для B=1, BF16 KV, 16 full attention layers, 4 KV-heads, D=256:
`2 * 16 * 4 * 256 * 2 = 65,536 bytes/token`; при 32,768 токенах — 2 GiB.
GDN FP32: `48*48*128*128*4 = 150,994,944 bytes = 144 MiB` per sequence.
Conv history estimate при K-1=3, BF16 и channels=10240: 2,949,120 bytes per sequence.
Последний estimate отражает выбранную history convention, не обещает layout конкретного backend.
Все значения — вывод из [S01], не hardware measurements.

`B*T*V*2` bytes full BF16 logits для T=32768,V=248320 — 16,273,899,520 bytes.
Генерации обычно нужен last-token projection output; all-logits opt-in. Это возможный расход API,
а не обвинение конкретного текущего движка в materialization такого массива.

Весовой нижний предел 27e9 * bits/8 не учитывает точное количество, vision/MTP, scales,
неоднородную precision и storage metadata. CLI намеренно возвращает `fit_verdict=UNKNOWN`.

## Защита узла

До больших allocations установить budget только из observed local data. Reserve — explicit user/project setting,
а не hardcoded «на Spark можно занять все 128». Ограничить test batch/context, проверять доступный диск, делать incremental load.
Не включать swap, overcommit, hugepages и system tuning автоматически. Слишком дорогую задачу остановить до загрузки.

## Политики аллокации

Начать с корректного working baseline pinned core, а не нового planner. Затем compare HOST/SHARED/DEVICE/pinned/managed
там, где driver поддерживает их. Synchronization должен гарантировать видимость, pool reuse — завершение всех readers.
Zero-copy когда возможно — optimization; observable CPU/GPU values и lifetime — contract.
Dynamic migration/NUMA-like идеи не включать без измерения page faults/transfer/access costs.

## Training budget

При условной схеме BF16 weights+BF16 grads+2 FP32 Adam states:
`27e9*(2+2+4+4)=324e9 bytes` без activations и optional master weights. Это не помещается в 128GB и не исправляется
перекладыванием state на CPU того же Spark. Поэтому большой first training target — LoRA/QLoRA,
при обязательной общей поддержке full training на малых сетях.

## Acceptance

OOM exception actionable; no process-wide corrupt state; next small operation works.
Cache clear не освобождает live arrays. Views keep base alive. Source checkpoint не перезаписывается ленивым save.
Метрики различают logical/allocated/reserved. Stress tests не превращаются в невольно destructive exhaustion.
