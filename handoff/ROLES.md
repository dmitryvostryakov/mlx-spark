# Роли и границы владения

| Роль | Основная ответственность | Не делает в одиночку |
|---|---|---|
| **Sol** | Интегратор, fork/build/namespace, core API, execution, transforms, nn, packaging | Не подтверждает собственный numerical/performance claim без review |
| **Terra** | Memory/UMA, CUDA kernels, GDN, quantization, MTP execution | Не меняет math/model semantics и tolerances ради скорости |
| **Luna** | Model audit, tokenizer/state/oracles, training recipes, vision, evaluation, benchmarks | Не объявляет inference-only path полноценным training/framework |

Распределение — engineering default, не оценка скрытых возможностей моделей с такими именами.
Если роль не справляется, передаётся конкретная задача с reproducer; нельзя менять сам product contract.

**Общие файлы под Sol:** AGENTS/CONTEXT, source locks, pyproject/CMake, public contracts, task state, release manifests.
**Terra-first paths:** native/cuda, future memory implementation, quantization low-level и GDN primitive kernels.
**Luna-first paths:** model fixtures, tokenizer/state tests, evaluation/quality/training examples и model audit docs.
Reference math изменяется с перекрёстной review Terra/Luna; root scope — только по owner decision.
