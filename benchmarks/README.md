# Benchmark scaffolding

Шаблон не содержит замеров и намеренно отвергается summary tool.
`tools/summarize_benchmark.py baseline.json candidate.json` обрабатывает только уже полученные measured records
с совпадающими model/input/precision/context/settings. Скрипт не запускает Qwen и не измеряет GPU.
Полный протокол — docs/BENCHMARK_PROTOCOL.md. Истинность hardware declaration и logs проверяет reviewer.

Не заполнять template предполагаемыми timings. После реализации модельного runtime добавить настоящий
runner с CUDA synchronization, resource budgets и immutable provenance. Эта работа относится к PERF.
