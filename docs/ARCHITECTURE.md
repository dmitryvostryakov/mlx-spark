# Архитектура: самостоятельный framework, один Spark

## Слои и направления зависимостей

Публичный Python/C++ API → array/function transforms/module layer → lazy graph/primitive registry →
CPU/CUDA execution и memory → hardware. Модельный пакет использует публичные/general operators сверху.
CLI/diagnostics наблюдают runtime; они не становятся частью tensor semantics.

`src/mlx_spark/core.py` — зарезервированная точка нашего API, а не proxy к внешнему MLX.
Будущий native `_core` собирается из проверенного импортированного ядра и своих изменений.
`nn` и `optimizers` — Python modules собственного дерева; контракты поведения не зависят от Qwen.
`reference/` — исключительно тестовые NumPy-oracles и не импортируется стандартным runtime.
`native/cuda/gdn_decode_reference.cu` — кандидат baseline, а не реализованный lazy primitive.

## Исходная кодовая база

Рекомендован controlled fork, а не clean-room rewrite. FND-05 импортирует source в checked-in дерево отдельным commit,
с лицензиями и исходным SHA; FND-06 делает namespace/build integration. До этого `.cache/upstream` — карантин
для source audit, не продуктовый runtime. Внешний installed mlx не нужен готовому wheel.

Не навязывать замену всех внутренних C++ names. Можно иметь internal `mlx::core`, но public CMake target `MLXSpark::Core`,
собственный soname/ABI boundary и Python module identity. Отдельно проверить serialization type names,
DLPack lifetime и nanobind registration. Automated source transforms применяются только после теста точного diff.

## Primitive contract

Имя/семантика, input/output specs, allowed layouts/dtypes, alias policy, device/stream policy,
forward implementations, transform rules, numeric policy и capability report. Shape inference не аллоцирует большие tensors.
Важна полная функция, включая state-output: GDN принимает/возвращает state; autograd видит нужные зависимости.
Обновление state in-place допустимо как optimization при доказанном отсутствии alias/gradient hazards, не как исходная семантика.

Forward dispatch выбирается по architecture/dtype/shape/layout/capabilities, не по имени модели.
Unsupported shape может идти в корректный generic path с явной diagnostic record; silent CPU fallback запрещён.

## Execution semantics

Lazy graph строится динамически. Materialization перед чтением хоста/сериализацией/синхронным benchmark объявляется явно.
Streams и events управляют dependency ordering и release/reuse буферов; completion worker не должен освобождать live storage.
Compiled graph cache включает relevant shape/dtype/layout/precision/toolchain features и имеет ограничение размера.
Статические адреса CUDA Graph не совместимы автоматически с растущим cache: рост/rebind invalidates capture либо использует
проверенную stable backing allocation.

## Memory

Shared physical RAM не отменяет типы аллокации, synchronization и ownership. Математический объект array может быть
доступен CPU/GPU через согласованный runtime, но нельзя обещать CPU-readable pointer для каждой device allocation.
Memory policy избирается capability+measurement, не эвристикой «UMA значит zero copy для всего».
Pool учитывает active/reserved/pending bytes, а модель — weights/KV/recurrent/conv/workspace.

## Модельный слой

Configuration/weight mapping/tokenizer/generation не живут в core. Generic norm/attention/GDN/conv primitives
составляются в Qwen architecture с explicit scaling, gates и positions. Модельный manifest перечисляет loaded,
excluded-by-mode и missing tensors. Text-only alpha исключает vision/MTP явно; полный релиз их проверяет.

## Будущая расширяемость без distributed кода

Разделить operator semantics и kernel implementation; хранить logical parameter axes в модели; versioned checkpoint
без «локальный pointer является идентификатором веса». Этого достаточно сейчас. DistributedTensor, communicator,
rank/world_size, remote allocation, network auto-discovery отсутствуют в первой реализации.

## Interop и общность

DLPack/NumPy bridges требуют ownership/stream tests; отсутствие transfer иногда возможно, но не гарантируется названием API.
PyTorch/Transformers нужны только для независимого oracle и quality benchmark. Ядро не знает HTTP, bots, retrieval,
private data, workflow router или внешние приложения.
