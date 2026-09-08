# Приёмка и уровни релизов

## Milestones

**Scaffold delivery:** документы, исходный каркас, reference tests и workflow tools. Это текущий ZIP.
**Native foundation:** собственное импортируемое ядро на GB10, basic arrays/train toy; API parity ещё может быть неполным.
**Qwen text alpha:** checked BF16 generation/state; не complete model/framework.
**Single-Spark v1:** полные обязательные gates по зафиксированному API/model contract; после него только возможен TP2.

## Required single-Spark gates

Source/toolchain lock; independent native package; public API parity; CPU/CUDA semantics;
VJP/JVP/vmap/higher-order; lazy/compile/streams; safe memory lifetime/OOM;
generic real training/checkpoint/resume; Qwen BF16 text/state; LoRA/QLoRA;
quant quality; vision/video; MTP rollback; numeric/security regressions;
performance no unexplained material regression; clean install/docs/examples; independent release review.
Точная machine-readable запись — configs/release-gates.json.

## Проход evidence checker

`tools/check_gate.py --evidence <real.json>` проверяет обязательные статусы, hash существующих artifacts,
real hardware declaration, immutable commit и независимость reviewer. Template в evidence намеренно synthetic.
Checker — не криптографическая attestation и не защита от сознательно сфальсифицированных логов.
Reviewer проверяет происхождение и содержимое, adequacy тестов, не только факт наличия файлов.

## Отчёт релиза

Что implemented/validated, exact environment, supported dtype/shape/context/mode tiers,
known limitations/bugs, results with raw links, upgrade/rollback instructions, notices/SBOM,
source ancestry, tested API inventory, package hashes и signature policy если используется.
Нельзя писать поддержку Qwen video от факта наличия vision_config. Нельзя писать training support от forward only.

## Установка и обратимость

Проверить install в новом env, import without upstream dependency, C++ consumer, документационные примеры,
локальный upgrade/rollback checkpoint compatibility и uninstall without damage.
Public package publish/GitHub create не входит в hand-off authorization.
