# Передача задачи

- Task / role / reviewer: FND-01 / Sol / Luna.
- Base commit / implementation commit: `e12c8cbe002b5c44db53ccd2c04c156ecebfe68c` /
  `9ec1195d4080cc822ce7d73f5eb17a3410168d29`.
- Scope и защищённые ограничения: полный standalone framework остаётся целью; один Spark/одна GB10;
  Qwen3.8-27B первая большая модель; TP2 полностью deferred.
- Изменённые implementation-файлы: `scripts/check_local.sh`, `tests/test_check_local.py`, `AGENTS.md`, `README.md`,
  `handoff/FIRST_SESSION.md`, `handoff/MASTER_PROMPT.md`, `evidence/BUNDLE_VALIDATION.md`,
  `tests/test_honesty_safety.py`; unsafe `evidence/validation/pytest.xml` удалён из current tree. Относительно base
  `tools/validate_plan.py` не изменён.
- Принятый interface/ADR: interface и ADR не менялись; startup требует Python 3.11+, harness поддерживает явный
  `MLX_SPARK_PYTHON`, а обязательные инструкции используют `python3`.
- Команды и exit codes: структурировано перечислены в `run.json`; два исходных failure, first-review logs и все
  remediation logs сохранены. Небезопасные JUnit XML удалены, безопасные raw text logs оставлены.
- Evidence paths + hashes: `evidence/runs/fnd-01/`; reviewed `SUBMISSION-2.sha256` и post-review `FINAL.sha256`.
- Что численно/аппаратно проверено: 49 CPU/reference tests и 1 C++ host contract test на Darwin arm64;
  аппаратная валидация DGX Spark не выполнялась.
- Что только реализовано, но не проверено: CUDA/model/framework runtime в этой задаче не реализовывались.
- Известные ошибки/risks: native `_core` отсутствует; Qwen/CUDA/training/performance неизвестны; memory fit UNKNOWN.
- Оставшиеся acceptance criteria: нет; final state update фиксирует approved review и task status.
- Следующий один конкретный шаг: FND-02 read-only inventory только на явно выбранном одном Spark.
- Можно ли интегрировать: yes — exact submission `455f84b` independently approved; scope остаётся scaffold-only.
