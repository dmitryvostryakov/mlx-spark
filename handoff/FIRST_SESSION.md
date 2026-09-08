# Первая рабочая сессия — точные шаги

## 0. Сохранить исходную доставку

Распаковать в новый пустой каталог. Проверить Python 3.11+ командой
`python3 -c 'import sys; assert sys.version_info >= (3, 11), sys.version'`, затем выполнить
`python3 tools/check_integrity.py` до любых изменений.
Сохранить оригинальный ZIP отдельно; после намеренных code edits original manifest ожидаемо перестанет совпадать.
Не «чинить» manifest ради сокрытия изменения; новый release manifest генерируется отдельно.

## 1. Прочитать только нужное

AGENTS.md, CONTEXT.md, PRODUCT_SPEC.md, MASTER_PLAN.md, planning/tasks/FND-01.md.
Затем `python3 tools/validate_plan.py` и `python3 tools/next_task.py --agent Sol`.

## 2. Локальные безопасные проверки

```bash
PYTHONPATH=src python3 -m mlx_spark status
PYTHONPATH=src python3 -m mlx_spark memory-estimate   --config configs/models/qwen3.8-27b.config.snapshot.json --tokens 32768
```

При уже доступных NumPy/pytest/compiler: `bash scripts/check_local.sh`.
Иначе isolated dev bootstrap по README с explicit network flag, не upgrade system Python.

## 3. На выбранном Spark

```bash
mkdir -p .runtime
PYTHONPATH=src python3 -m mlx_spark doctor > .runtime/host-inventory.json
```

Это read-only query, не GPU stress/validation. Оценить actual driver/toolkit/cuDNN/compiler.
Никакой проверки QSFP или второго узла. CUDA probe build только позже по MEM-01/GDN-02:
`bash scripts/probe_spark_cuda.sh --run-on-selected-spark` после review compatibility.
Exit77 означает not run, не successful hardware gate.

## 4. Источники

```bash
python3 tools/resolve_sources.py --allow-network --output .runtime/source-lock.resolved.json
```

Просмотреть exact revisions, notices/config diff, создать reviewed copy lock с `review_state=approved` и
непустым `review_evidence` (путь на содержательный review document). Не менять status без review.
`fetch_upstream.py` загружает source-only в новый каталог; не устанавливает library и не скачивает Qwen weights.

## 5. Первая передача

Обновить CURRENT.md с observed environment/commands/errors; FND-01 done после review;
FND-02/03 по факту. Не менять все todo на done после одного тестового запуска.
