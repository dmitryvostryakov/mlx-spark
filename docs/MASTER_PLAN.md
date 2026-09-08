# Максимально подробный план реализации

## Структура выполнения

План — DAG из 91 карточки, а не календарное обещание. 85 задач относятся к одному Spark, 6 закрыты до TP2.
`planning/tasks.json` содержит зависимости; `TASKS.csv` удобен для просмотра; каждый task имеет отдельную карточку.
Числа задач описывают этот hand-off и не являются оценкой длительности. Объём/риски уточняются по evidence.

## M0. Защищённая исходная точка — FND-01…03

Принять scope, проверить bundle, сделать harmless inventory выбранного Spark, разрешить immutable source/model references.
Цель — знать, что именно собирается, для какой системы и почему. Недостающий доступ оставляет hardware task blocked,
но не останавливает CPU/reference work. Нельзя выбирать CUDA toolkit по памяти о прошлых беседах.

Выход: reviewed lock, model metadata diff, hardware inventory, resource budget, минимальный checkpoint контекста.

## M1. Независимая собираемая основа — FND-04…07

В отдельной среде сначала получить неизменённый upstream baseline. Затем импортировать лицензированный source в собственное
дерево и собрать собственную библиотеку/namespace. Не делать package alias на installed mlx.
Binding/module names, pyproject metadata, native targets, install rpaths и serialization type names проверяются отдельно.

Выход: native `mlx_spark` в чистом окружении, provenance commit, exact API inventory. Пока это не promise полного parity.

## M2. Общие вычисления и память — CORE/MEM/EXEC

CORE закрывает semantics и operator coverage: scalar/empty/views/dtypes/indexing, arithmetic/reductions,
matmul/conv/norm/attention/random/linalg/FFT/interop. MEM — capability-driven allocations, stream-safe reuse,
accounting, bounded memory pressure, streaming load/save, stress. EXEC — lazy execution, streams,
shape-dependent compile caches и только затем CUDA Graph replay.

Эти треки можно распараллелить по изолированным worktrees после готовности исходников и договорённости о contracts.
Нельзя делать allocator API, затем менять все arrays под красивую UMA гипотезу: correctness visibility измеряется прежде.

Выход: common tensors/ops на CPU и GB10, численная политика и базовые safe memory semantics.

## M3. Настоящие transforms и обучение — AD/NN

VJP, JVP, vmap, higher-order и композиция compile/grad — равноправная часть framework.
Optimized primitive без backward не должен перехватывать training вызов с неверным результатом.
Modules/parameters/buffers, optimizers, RNG и checkpoint/resume проверяются на малых независимых сетях.
Падение loss в bundled NumPy fixture не закрывает эту фазу: она лишь даёт внешний ожидаемый trajectory.

Выход: пользовательский MLP/conv/recurrent example реально обучается через наш API; save-resume воспроизводим.

## M4. Correctness-first Qwen text — QWN

QWN-01…03 можно готовить как аудит источников до native выполнения. Интеграция начинается после модулей ядра.
Полная инвентаризация checkpoint, exact tokenization и explicit exclusions text-only; слои собираются из generic operators.
Сравнение выполняется от слоя к слою и от whole prefill к chunked/cache continuation, а не только decoded текстом.
Контекст растёт от 128 к 1K/4K/8K/32K после budget check; native max advertised не объявляется verified автоматически.

Выход: корректный BF16 text alpha, явный model manifest, неотключённые безопасные error checks.

## M5. Производительные операции — GDN/EXEC/PERF

GDN — сильный кандидат, поскольку просмотренный MLX-LM generic path и specialized Metal path различаются [S10].
Но приоритет final optimization устанавливается реальным профилем наших source/model versions.
Сначала scalar-gate FP32 correctness candidate, затем BF16 inputs/FP32 state, chunked prefill, backward и production dispatch.
Compile/fusion/graph capture принимаются при сохранении semantic equivalence и memory bounds.

Выход: measured single-Spark improvement или честное объяснение отсутствия выигрыша. Улучшение microkernel не равно model speedup.

## M6. Quantization и полезное дообучение — QTZ/TRAIN

Один documented quant format первым; packing/scales/groups/rounding/exclusions известны.
Данные calibration отделены от holdout. Converter не удваивает весь checkpoint в памяти и не перезаписывает source.
LoRA BF16 затем QLoRA; проверить upstream frozen weights, input gradients through quantized ops,
state gradients и exact checkpoint/resume. Full 27B Adam memory не маскировать «CPU offload» в ту же память Spark.

Выход: реально работающие mode-specific recipes с quality/memory/performance evidence.

## M7. Полная поддержка первой модели — VIS/MTP

Vision processor/encoder/projector и multimodal positions; staged video handling с ограничениями размеров.
MTP weights/algorithms; exact speculative acceptance отдельно для greedy и sampling; откат всего hybrid state.
MTP может не ускорить workload и потому имеет explicit enable/disable и evidence, а не всегда-on marketing default.

Выход: model-support manifest без silent dropped tensors и без unsupported multimodal/MTP claims.

## M8. Продуктовый single-Spark release — PKG

Закрыть remaining API parity, C++ SDK example, чистую установку, security, pinned deps/SBOM,
manual trusted hardware CI, документацию и independent review. `check_gate.py` проверяет формат/evidence;
reviewer проверяет подлинность logs и достаточность проверки. Нет synthetic/skip loopholes.

Release версии внутри проекта можно собирать локально. Внешняя публикация требует отдельного разрешения.
Только этот milestone открывает обсуждение практической реализации TP2.

## M9. Отдельная следующая фаза — TP2

6 карточек лежат в backlog только как outline: unlock, network/transport measurement, tensor sharding,
collectives/launch, numerical/performance comparison, optional distributed package. Не исполнять их сейчас.
Не добавлять ни world_size в обычный single-node API, ни NCCL/DOCA setup в M0.

## Приоритет при ограниченном контексте агента

Сначала close blocker ближайшего milestone, затем complete vertical slice, затем оптимизация.
Не распыляться между 91 задачей. Первая исполняемая задача — FND-01; helper выдаёт только ready tasks.
После каждого task сохранять diff, tests, evidence и next 1–3 tasks. Расширение scope только через ADR/owner decision.
