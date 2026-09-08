# Численная приёмка

## Не путать уровни evidence

Mathematical oracle с float64, generic framework CPU, native CUDA operator, compiled pipeline и целая Qwen — разные уровни.
Согласие двух реализаций с общим скопированным bug не независимая проверка. Поэтому использовать analytical/finite difference
на маленьких задачах, separately maintained pinned reference и full-model behavioral/logit tests.

## Политика точности

BF16 baseline model weights/activations, FP32 recurrence и необходимые reductions — стартовая гипотеза,
которую сверяют с checkpoint/source. TF32, fast-math, FMA/reduction order, denorm handling и deterministic mode
фиксируются в run manifest. Tolerances зависят от функции/conditioning/dtype; один global atol=1e-2 недопустим.

Bundled oracle finite differences использует eps=1e-6 и rtol=2e-6/atol=2e-8 на small float64 fixtures.
Это прошедший test setting, **не** Qwen BF16 acceptance threshold. CUDA toy candidate имеет свой loose absolute bound
только для одного синтетического FP32 случая; production tolerances ещё предстоит откалибровать до candidate evaluation.

## Метрики

Max/median absolute error, scaled relative error with documented denominator, finite/NaN mask,
layerwise norm/error drift, logits distribution divergence, NLL на fixed token stream, top-k changes,
task behavior и long-horizon state equivalence. Cosine/top1 alone не ловят все ошибки.
При stochastic generation сравнивать корректность distribution и reproducible seed semantics, не требовать
одинаковой строки между разными quantizations как единственного критерия.

## Regression matrix

Scalar/empty/broadcast/negative/strided/tail inputs; FP16/BF16/FP32/complex where applicable;
zero/nonzero initial state; long recurrence; prefill/chunk/decode; masks/padding/branches;
training vs inference; eager vs compile; before/after serialize; before/after quantization;
image/video processor edge cases; MTP accept/reject every position.

## Допуски и независимость

Reviewer фиксирует tolerances/evaluation fixtures до оценки нового kernel, записывает rationale и version.
Если ошибка не укладывается, сначала identify root cause (scale, norm, reduction, mask, state) и minimal reproducer.
Нельзя расширить tolerance без объяснения и назвать unchanged passing gate. Quality thresholds calibration/holdout
не смешивать; не подбирать prompts под удачную генерацию.

## Работа без full BF16 oracle в памяти

Для 27B сначала проверить фактический бюджет, не обещать full model fit. При невозможности целого oracle использовать
layerwise streamed evaluation и маленькие token fixtures, сохраняя независимые outputs. Не подменять это сравнением
только двух quantized conversions. Формат reference artifacts должен хранить source SHA/precision/commands.
