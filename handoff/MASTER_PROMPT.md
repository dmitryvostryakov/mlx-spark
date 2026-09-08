# Стартовый prompt для 5.6-Sol / Terra / Luna

Ты работаешь в корне распакованного MLX-Spark hand-off. Прочитай `AGENTS.md` и `CONTEXT.md`.
Проект — полноценная самостоятельная Apple-like альтернатива MLX для одного DGX Spark / GB10.
Первая большая модель Qwen/Qwen3.8-27B; обучение, autodiff, compile и general framework API обязательны.
TP=2 только после стабильного single-Spark release. Не проектируй прикладной inference-server вместо framework.

Пакет содержит scaffolding, а не готовое вычислительное ядро. Не выдавай NumPy oracle или внешний installed MLX за
продукт. Нативный `_core`, Qwen inference и GPU training ещё надо реализовать. На неподтверждённом железе не заявляй benchmark.

Начни как Sol-интегратор:
1. Прочитай `START_HERE.md`, `docs/PRODUCT_SPEC.md`, `docs/MASTER_PLAN.md` и `handoff/AGENT_PROTOCOL.md`.
2. Проверь Python 3.11+ командой `python3 -c 'import sys; assert sys.version_info >= (3, 11), sys.version'`, затем
   выполни `python3 tools/check_integrity.py`, `python3 tools/validate_plan.py`, `python3 tools/next_task.py --agent Sol`.
3. При доступных dev dependencies выполни `bash scripts/check_local.sh`. Не ставь ничего в системный Python.
4. Возьми FND-01. Запиши checkpoint по шаблону. Затем FND-02 только на явно выбранном одном Spark.
5. Source/metadata resolution делай с explicit opt-in и review; full model download не входит в bootstrap.

Работай по одной готовой карточке с prerequisites. Каждая карточка заканчивается code/tests/raw evidence/review,
а не отчётом «план готов». Дальнейшие изменения framework выполняй в текущей сессии до доступной законченной части;
если блокирует аппаратный доступ, сохрани reproducer и продолжи независимую разрешённую работу без fake results.

При нескольких агентах используй roles/prompts в handoff. Sol интегрирует; Terra ведёт CUDA/memory/quant/MTP;
Luna — model correctness/training/evaluation. Это названия ролей, не assumptions о закрытых моделях/API.
Не вызывай несуществующие модели/команды и не объявляй, что другие агенты уже выполнили работу.

Не спрашивай владельца заново о цели, Qwen, одном Spark или порядке TP. Не меняй системные сервисы/драйвер/ОС/сеть.
Не получай доступ ко второму Spark. Не публикуй репозиторий, пакет или private данные.
После каждого завершённого task обнови tasks.json, checkpoint и CONTEXT с фактами, командами и следующими 1–3 задачами.
