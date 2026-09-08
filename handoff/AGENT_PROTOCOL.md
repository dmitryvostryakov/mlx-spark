# Протокол реализации несколькими агентами

## Зачем

Разделить работу и independent review без общей скрытой памяти и без одновременной правки ядра.
Протокол не зависит от vendor/model API. Имена 5.6-Sol/Terra/Luna используются как договорённые рабочие роли.
Один агент может выполнять роли последовательно; при этом independent review желательно поручать отдельной сессии/модели,
а не утверждать независимость просто от смены названия в одном ответе.

## Выбор задачи

JSON DAG — source of truth. Ready = phase single_spark, status todo/ready, все deps done с evidence.
`next_task.py` read-only, не claim scheduler. Claim фиксируется отдельным `handoff/claims/<task>.json` через
Git commit/PR или согласованный интегратором документ. До claim убедиться, что task не взят другим.
В реальном shared filesystem atomic exclusive-create claim предпочтительнее гонки с обычным overwrite.
Смена ownership только через Sol и записанное основание.

## Рабочие деревья

Каждый агент отдельный worktree/branch после инициализации repository владельцем/интегратором.
Shared files (source locks, pyproject, native build, root contracts) меняет Sol после review.
Terra не расширяет dtype/layout/alias contract в kernel без согласования consumers; Luna не меняет tolerances
ради прохождения Terra kernel. Interface change оформляется ADR и failing contract test до implementation.

## Один Spark — одна измерительная задача

Параллельная подготовка кода разрешена в отдельных worktrees. CUDA benchmarks/profile/heavy training serialised:
один агент владеет ресурсом; второй не мешает clocks/thermal/memory. Build job count ограничивать бюджетом.
Скрипт не должен убивать чужую задачу для получения «чистого» benchmark. При занятости ждать не обещаем —
выполняем другую CPU задачу либо заканчиваем с сохранённым blocked status.

## Contract-first цикл

Task brief → reviewed interface/tests → минимальная implementation → targeted tests → full applicable suite →
evidence → independent review → integration → context update. Никаких больших несвязанных reformat/rename в одном task.
Review проверяет failure paths/unknowns/precision и границы scope, не только happy-path latency.

## Формат передачи

Task ID, base/implementation commits, modified paths, commands and exit codes, observed results,
planned/unrun tests, known defects, proposed scope changes, exact next action. Использовать HANDOFF_TEMPLATE.md.
Не передавать только «всё работает» или огромную неструктурированную историю. Context summary не заменяет raw logs.

## Ошибки и retries

При build failure сохранять first root error и environment; не многократно переустанавливать весь стек.
При numeric failure minimal reproducer + layer/state diff. При OOM уменьшить только локальный experimental case
и записать original requested budget; не маркировать большой case passed. При unsafe action requirement — запросить
конкретное разрешение, не общий повторный scope discussion.

## Merge and done

Reviewer отличен от implementer для release-signoff. Task status done только при всех acceptance criteria;
partial work = in_progress/blocked с оставшимися условиями. Карточки — baseline spec, live status JSON.
На final single-Spark release проверяются все required gates, не «процент закрытых задач».
