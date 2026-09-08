# CONTEXT — компактное состояние для продолжения

**Дата фиксации:** 2026-09-08. **Текущая стадия:** FND-02 принят на выбранном DGX2; native framework не завершён.

## Зафиксировано владельцем

MLX-Spark — самостоятельная Apple-like альтернатива MLX, не сервер и не wrapper. Полнота включает обучение.
Старт: один DGX Spark. Первая большая модель: Qwen/Qwen3.8-27B. Два Spark с QSFP/ConnectX-7 есть в наличии,
но реализация/диагностика TP=2 — только после стабильного single-node release. Другие DGX/Blackwell позже.
Проект не связывать с прикладным агентным приложением. Не спрашивать эти решения заново.

## Инженерные defaults этого hand-off

Контролируемый fork pinned MLX как исходный материал; свой namespace `mlx_spark`, native artifact и SDK.
Python/C++ сначала, ARM64 Linux/GB10 — target; CPU-only другие машины только для scaffold/reference работы.
BF16 model baseline, FP32 recurrent state, затем один verified quant format. Никаких speedup guarantees.
Sol — интегратор/core; Terra — CUDA/memory/quant/MTP; Luna — model correctness/training/evaluation.
Это роли, не утверждение о характеристиках моделей с такими названиями. Подробности в handoff/ROLES.md.

## Подтверждённые источниками сведения

Qwen config декларирует qwen3_5, 64 слоя: 48 linear/GDN + 16 full attention; hidden 5120,
attention heads 24, KV heads 4, head_dim 256; GDN Hk16/Hv48/Dk128/Dv128; vision и один MTP-layer. [S01]
MLX имеет CUDA backend. Source candidate: `365bd0fbac2e96631a1b2c4a34ca5a0771cdfde5`,
наблюдался в upstream 2026-09-08; это НЕ tested target build. [S03,S04]
GB10 — compute capability 12.1; Spark — shared CPU/GPU memory. Memory allocations всё равно имеют разные access semantics. [S05,S06,S07]
Источники и точные URLs: `docs/SOURCES.md`.

## Что в ZIP реально реализовано

CLI status/doctor/memory estimate; config validator; NumPy GDN forward+analytic VJP и GQA oracle;
reference snapshot/checkpoint helpers; C++ host contracts; opt-in source resolver; task DAG and release evidence checker.
CUDA FP32 decode/probe/test исходники есть, но не собраны/не запущены на GPU в среде подготовки.
Production tensor core/nn/optimizers/Qwen loader/generation/training отсутствуют; интерфейсы fail clearly.
47 Python-тестов + 1 C++ host test прошли; wheel собран и установлен в чистое изолированное окружение.
Это проверка scaffold/reference, не native CUDA/Qwen. Подробности: evidence/BUNDLE_VALIDATION.md.

## Выполнено после доставки

FND-01 принят independent review. Исходный ZIP проверен по 233 manifest entries и зафиксирован как base commit.
Startup path теперь явно требует Python 3.11+, full local suite проходит: 49 Python tests + 1 C++ host test.
Shareable evidence очищен от JUnit hostname metadata с сохранением исходных bytes в ZIP/base history; добавлен regression.
Evidence и review: `evidence/runs/fnd-01/`. Это по-прежнему только scaffold-tested, не native/hardware-validated.

Для FND-02 реализован и локально протестирован обезличенный read-only doctor: OS/DGX OS, memory/current cgroup,
selected filesystem, GPU/driver, toolkit, compiler/CMake и cuDNN. Implementation commit:
`624eb88bc5c31a628cbc15180db21ec5b6dbd3da`; 11 targeted doctor tests проходят.
Independent implementation re-review approved.

Через owner-provided `ssh dgx2` standalone doctor выполнен read-only из stdin без remote install/write. Observed:
Linux aarch64, NVIDIA DGX Spark (SW build 7.2.3, OTA 7.5.0), Ubuntu 24.04.4, одна NVIDIA GB10/sm_121,
driver 580.159.03, Python 3.12.3, glibc 2.39, GCC 13.3.0, CMake 3.28.3. MemAvailable 113.51 GiB,
finite cgroup limit не наблюдался, swap 0; selected filesystem free 582.45 GiB. `nvcc` unavailable, cuDNN unknown.
Evidence: `evidence/runs/fnd-02/inventory.json`.

Предложенный foundation budget: project working set <=80 GiB при reserve 32 GiB; project disk <=256 GiB при
free-space floor 256 GiB; build cache <=96 GiB; build jobs <=4. Большие веса не разрешены этим budget.
Hardware facts, budget arithmetic и evidence-fidelity remediation независимо приняты для state `7b0c142`.
Replayable validator, четыре boundary tests и full scaffold (64 Python + 1 C++) проходят. FND-02 status `done`.

## Unknown / не угадывать

Actual CUDA toolkit version (nvcc unavailable) и cuDNN version; exact immutable HF model revision; production API
inventory и package-name availability; CUDA compile/runtime correctness; Qwen quality/speed;
конкретный performance target до baseline.

## Лицензия

Оригинальный код MLX-Spark распространяется под Apache-2.0. Это не отменяет обязательства сохранить отдельные
лицензии и notices для любого будущего импортированного кода; точная provenance-policy — `LICENSE-DECISION.md`.

## Следующее

1. FND-03: resolve/review exact sources и metadata с отдельным explicit network opt-in.
2. Затем FND-04: isolated pinned upstream baseline build на DGX2 в пределах принятого budget.
3. TP2 остаётся закрыт до стабильного принятого single-Spark release.

Live tasks: `planning/tasks.json`; current session: `handoff/checkpoints/CURRENT.md`.
Не загружать все 91 карточку в один контекст; читать только текущую и необходимые зависимости.
