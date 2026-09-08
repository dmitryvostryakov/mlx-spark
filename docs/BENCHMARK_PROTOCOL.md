# Протокол benchmark одного DGX Spark

## Цель

Получить воспроизводимые факты, где MLX-Spark корректен, быстрее/медленнее и сколько памяти использует.
Не ставить выдуманные target tok/s. Baseline — неизменённый pinned MLX CUDA, candidate — наш exact commit.
Внешний движок допустим как дополнительный ориентир, не как dependency продукта или доказательство совпадения качества.

## Run manifest

Revision/source/toolchain/driver/device/profile, quantization map и hash weights/tokenizer/config,
exact input token IDs hash, prompt/output lengths, seed, sampling/reasoning configuration, context/window,
batch/concurrency, KV/state dtype, math mode, compile/capture settings, warmup и trial count,
clocks/power/temperature telemetry если доступны read-only. Никаких guessed current specs.

## Измерять отдельно

Cold model load (включая/исключая disk-cache оговорено), conversion, tokenizer/processor;
prefill latency/tokens/s; TTFT; steady decode step latency/tokens/s; full generation wall time;
training step time и examples/tokens per second; peak host/UMA/device metrics и allocated/reserved/workspace.
Не складывать разные память-источники как независимые pools. Time CUDA измерять с synchronize/events
там, где требуется actual elapsed compute; Python enqueue time отдельно и не называется inference latency.

## Набор workload

Текст prefill128/1K/4K/8K/32K, output128/256, batch1 baseline и small batch2/4 после budget.
Decode with growing cache; prompt chunk boundaries; GDN long-state; LoRA steps; explicit quant format;
vision/video bounded fixtures; MTP off/on одинаковые model/sampling conditions.
Advertised262K не test obligation до безопасного расширения бюджета и отдельного declared support tier.

## Повторы

Дизайн warmup/trials фиксировать до результатов; стартовый candidate protocol — 3 warmup, 10 paired trials для коротких cases,
более дорогие cases отдельным режимом с меньшим count и явной неопределённостью. Это предлагаемые settings, не measurement.
Сравнивать median, p95, spread/CI при достаточных данных; не лучший единичный прогон.
Не выполнять concurrent compile или чужой benchmark на том же GPU во время сравнительного измерения.

## Приёмка performance

Сначала numerical/quality gate, потом скорость. Значимое улучшение требует стабильного positive paired delta
за пределами шума. Материальная регрессия не допускается без approved tradeoff/отключаемого fast path.
Конкретный numerical threshold установить после baseline variance, до оценки candidate — не выбрать выгодный post-hoc.
Отсутствие speedup допустимо для correctness milestone, но не повод писать «оптимизация ускоряет».

## Энергия

Если доступна корректная telemetry, энергия — integral watts over seconds, в joules/token.
Watts/token как название эффективности некорректно. Редкое sampling мощности не даёт точного per-token energy;
тогда power/energy помечается approximate или omitted.

## Evidence

Raw measurements immutable CSV/JSONL + run manifest + commands + profiler notes + independent review.
В ZIP нет измерений GB10. CPU NumPy fixtures никогда не попадают в таблицу Spark throughput.
