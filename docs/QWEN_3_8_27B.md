# Qwen3.8-27B: модельная спецификация и доказательства

## Источник истины

Репозиторий `Qwen/Qwen3.8-27B`, immutable revision нужно разрешить и проверить перед weights.
Config snapshot в bundle — нормализованное представление фактов из опубликованного config на 2026-09-08 [S01].
Он не гарантирует original byte hash HF, exact parameter count или compatibility installed libraries.
Model card подтверждает native image/video и MTP-направление; конкретные веса/архитектуру проверяет loader audit [S02].

## Размеры, которые нельзя выводить эвристически

64 layers: 48 linear_attention и 16 full_attention. Hidden 5120; FFN intermediate 17408.
Full attention: 24 query heads, 4 KV heads, D=256. GDN: Hk=16, Hv=48, Dk=Dv=128, convolution kernel=4.
Рекуррентный state dtype в config — FP32. Vocabulary 248320; text max positions 262144.
Есть `attn_output_gate`, `output_gate_type=swish`, partial/multimodal RoPE; language model не единственный компонент. [S01]

**Не использовать `hidden_size // num_attention_heads` вместо head_dim.** Обратные допущения способны дать
работающий по shapes, но неверный математически код. Attention output gate тоже не optional optimization.

## Инвентаризация tensors

Для каждого checkpoint key сохранить shape/dtype/nbytes/shard и ожидаемую роль: embedding, language layer,
normalization, convolution, gate, vision, projector, MTP, output projection. Неисвестный/missing key — error до review.
Text-only alpha разрешает исключения только через explicit mode manifest; число исключённых tensors/bytes выводится.
Нельзя беззвучно sanitise away vision/MTP и объявлять complete model support. В просмотренной MLX-LM реализации
такие фильтры присутствуют; их нужно переосмыслить, а не копировать как продуктовый контракт. [S11]

## Transformer block checklist

Norm weight convention (unit-offset или нет), epsilon, accumulation dtype; q/k normalization и единственное место
readout scaling; packed projections and gate order; causal convolution history; GDN update order;
attention causal mask и KV offsets; partial/mRoPE position composition; residual/FFN gating;
final norm/output projection and tied/untied embeddings. Проверять exact pinned reference, не соседнюю Qwen-version.

## State invariants

Whole prefill == chunked prefill+continuation в установленной numeric policy.
Masked token не должен обновлять recurrence/conv/position там, где определён padding skip.
Branch/resume восстанавливает полный consistent state, а не только KV length.
Random generation state сохраняется отдельно от model recurrence. Смена checkpoint/quantization не переиспользует старый cache.

## Tokenizer, reasoning и output

Сохранить tokenizer, chat template, generation defaults и special-token mapping на той же revision.
Эталонные тесты подают одинаковые token IDs. Для user examples reason/output settings явно фиксируются,
иначе длина генерации и speed сравнения несопоставимы. Tokenization и модельное время измерять раздельно.
Нельзя корректность модели оценивать только красивым одним русским ответом.

## Проверка по слоям

Tiny shape references → operator outputs → отдельный layer → первые слои/full forward → cached decode →
long sequences → training gradients → quantization → vision/MTP. Layerwise comparison включает relative/absolute
error summaries, cosine только как дополнительную метрику, и logits/NLL. Top-1 match сам по себе недостаточен.

## Supported modes

Text BF16 baseline; weight-only quantization после quality gate; LoRA BF16 и QLoRA после input-gradient проверки;
image/video inference после processor/encoder/position tests; MTP inference после exact state rollback.
Обучение vision/MTP не обещается автоматически от поддержки их forward: capabilities разделены.
До полного release явно указать какие training modes охвачены; full-param 27B training зависит от физического бюджета.
