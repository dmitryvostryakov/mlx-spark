# QWN-01 — Аудит checkpoint и семантики архитектуры

**Фаза:** single_spark · **Владелец:** Luna · **Reviewer:** Sol · **Статус:** todo

## Входные условия
Зависимости: FND-03. Статус зависимости `done` действителен только с evidence и review.
Обязательный контекст: `AGENTS.md`, `CONTEXT.md`, `handoff/AGENT_PROTOCOL.md`, применимая спецификация из `docs/`.

## Реализация
Сопоставить pinned config, weight index, tokenizer/chat template и reference implementation. Проверить qwen3_5 dispatch, gates, RoPE, norm conventions, vision/MTP presence.

## Приёмка
Model spec содержит source links, exact revisions, tensor key classes и unknowns; никаких выводов только по имени 27B.

## Порядок работы
1. Выписать конкретные файлы изменения и новые тесты до кода. Сверить владельцев через hand-off.
2. Воспроизвести baseline/ошибку или добавить failing contract test. Не скрывать отсутствие оборудования skip-результатом.
3. Реализовать минимальный завершённый вертикальный участок без соседних задач и архитектурного scope creep.
4. Прогнать targeted tests, затем `bash scripts/check_local.sh`; для native/model работы — реальные соответствующие аппаратные тесты.
5. Передать diff, команды, raw logs и ограничения reviewer. После review обновить task status и CONTEXT/current checkpoint.

## Обязательные evidence
Каталог `evidence/runs/qwn-01/`: `run.json` с revision/toolchain/hardware/командами; неизменённые stdout/stderr; тестовый отчёт; численные результаты, если применимо; review note.
Пути для будущих тестов агент создаёт в ходе задачи. Отсутствующий planned test не считается выполненным.

## Запреты
Не менять допуски ради green. Не считать analytical NumPy fixture framework training. Не выдавать candidate CUDA за проверенный.
Не устанавливать драйверы, не менять ОС, сеть или существующие сервисы. Не публиковать репозиторий, веса или пакет.
Не вводить TP2/NCCL/SSH-зависимости в текущую задачу.

## Stop / escalation
Остановить только заблокированную часть при несовместимых исходниках, недостающем доступе, OOM за пределами budget или расхождении semantics.
Записать минимальный reproducer и продолжить независимую разрешённую работу. Не придумывать значения версий/benchmark.
