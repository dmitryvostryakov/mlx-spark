# Полная Qwen: vision/video и MTP

## Почему это не необязательный маркетинговый пункт

Qwen3.8-27B опубликована как vision-language модель; config содержит vision и MTP [S01,S02].
Text-only — допустимая alpha, но «полная поддержка Qwen3.8-27B» требует явной реализации/валидации компонентов.
Не выбрасывать их weights через sanitizer без сообщения и не выдавать external service за native поддержку.

## Vision

Pin processor/tokenizer/image pipeline. Resize/crop/interpolation/color/layout/normalization/patching и special tokens
должны совпадать с oracle. Fixtures local synthetic, без network image retrieval. Ограничения dimensions/bytes/frame counts
проверяются до выделения гигантских buffers. Encoder/projector проверяются layerwise.
Multimodal positional encoding и visual token placement проверяются отдельно от text-only RoPE.

## Video

Явная frame-sampling policy и timestamps, temporal patch handling, context/memory budget.
Контейнеры/декодеры — supply-chain input, их не требуется реализовывать с нуля, но runtime не принимает безлимитный media payload.
Простые deterministic synthetic sequences подходят для теста processor, но не доказывают semantic video quality без model oracle.

## MTP

Audit exact checkpoint/algorithm. Различать head forward, draft generation, verification и acceptance scheme.
При greedy проверить точное совпадение с target continuation. При stochastic acceptance нужна корректная distribution;
«похожая генерация быстрее» не доказательство exact speculative decoding.
Full hybrid state rollback включает GDN/conv/KV/positions/RNG. Reject at every position — mandatory fixture.

## Производительность и обучение

MTP off — обязательный стабильный путь. Включение по умолчанию только после измеренного end-to-end преимущества
на объявленном workload; учитывать overhead/acceptance/memory. Forward support vision/MTP не означает
проверенное fine-tuning этих компонентов. Соответствующие training capabilities документируются отдельно.
