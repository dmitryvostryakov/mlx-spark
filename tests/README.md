# Что доказывают эти тесты

Существующий набор проверяет **scaffolding**, валидацию конфигурации, арифметику памяти,
математические NumPy-эталоны, analytic GDN VJP, snapshot semantics, честность статусов и DAG плана.
Это не тесты native MLX-Spark, не full Qwen, не training framework и не аппаратный benchmark.

Будущие каталоги добавлять по задачам: `tests/core/`, `tests/autodiff/`, `tests/runtime/`,
`tests/models/qwen3_8/`, `tests/training/`, `tests/quantization/`, `tests/packaging/`.
Нельзя создавать пустые passing тесты или `pytest.skip` для получения зелёного release gate.
GPU tests запускаются на явно выбранном одном Spark. CPU-only CI не подтверждает GPU поддержку.
