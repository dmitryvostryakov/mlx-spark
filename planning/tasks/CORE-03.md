# CORE-03 — Индексирование и обновления

**Фаза:** single_spark · **Владелец:** Sol · **Reviewer:** Luna · **Статус:** todo

## Входные условия
Зависимости: CORE-02. Статус зависимости `done` действителен только с evidence и review.
Обязательный контекст: `AGENTS.md`, `CONTEXT.md`, `handoff/AGENT_PROTOCOL.md`, применимая спецификация из `docs/`.

## Реализация
Срезы, gather/scatter, repeated indices, negative strides, masks, broadcast, array.at и копии. Семантика repeated indices соответствует pinned reference.

## Приёмка
Рандомизированные тесты и VJP hooks для индексируемых операций; нет unsafe views.

## Порядок работы
1. Выписать конкретные файлы изменения и новые тесты до кода. Сверить владельцев через hand-off.
2. Воспроизвести baseline/ошибку или добавить failing contract test. Не скрывать отсутствие оборудования skip-результатом.
3. Реализовать минимальный завершённый вертикальный участок без соседних задач и архитектурного scope creep.
4. Прогнать targeted tests, затем `bash scripts/check_local.sh`; для native/model работы — реальные соответствующие аппаратные тесты.
5. Передать diff, команды, raw logs и ограничения reviewer. После review обновить task status и CONTEXT/current checkpoint.

## Обязательные evidence
Каталог `evidence/runs/core-03/`: `run.json` с revision/toolchain/hardware/командами; неизменённые stdout/stderr; тестовый отчёт; численные результаты, если применимо; review note.
Пути для будущих тестов агент создаёт в ходе задачи. Отсутствующий planned test не считается выполненным.

## Запреты
Не менять допуски ради green. Не считать analytical NumPy fixture framework training. Не выдавать candidate CUDA за проверенный.
Не устанавливать драйверы, не менять ОС, сеть или существующие сервисы. Не публиковать репозиторий, веса или пакет.
Не вводить TP2/NCCL/SSH-зависимости в текущую задачу.

## Stop / escalation
Остановить только заблокированную часть при несовместимых исходниках, недостающем доступе, OOM за пределами budget или расхождении semantics.
Записать минимальный reproducer и продолжить независимую разрешённую работу. Не придумывать значения версий/benchmark.
