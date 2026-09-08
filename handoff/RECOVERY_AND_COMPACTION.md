# Возобновление после смены агента или потери контекста

Прочитать AGENTS/CONTEXT → CURRENT checkpoint → текущую карточку → последний hand-off → review/evidence.
Сверить git status/diff (если repo инициализирован); не overwrite незакоммиченные файлы другого агента.
Определить real task state по JSON и artifacts, не по оптимистичному старому тексту.

Если checkpoint и код расходятся: восстановить минимальные факты через тесты и команды; различие записать.
Если нет GPU: аппаратные claims остаются unverified. Если source lock null/expired: не выбирать новую версию молча.
Если был OOM или crash: сначала tiny repro с безопасным budget, не повторять full load бесконечно.

Контекстное окно — ресурс. Не копировать сюда весь docs/task tree. В main context держать goal, fixed constraints,
current task, interfaces, commands/results и next3. Исходники/docs/reports открывать адресно.
Через завершённую карточку или ~10 значимых команд обновить checkpoint; это guideline, не скрипт background monitoring.
