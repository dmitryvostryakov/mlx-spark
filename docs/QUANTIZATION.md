# Квантование без потери управляемости

## Первый формат

Сначала выбрать один documented format после working BF16 baseline. Groupwise affine weight-only 4-bit —
кандидат defaults, не обязательная победа над FP8/NVFP4. INT4 packing и NVFP4 не эквивалентны.
Поддержка Blackwell arithmetic не гарантирует быстрый правильный kernel для любого storage layout.

## Контракт формата

Group size, axis, scale dtype, zero-point/bias definition, signedness, rounding/ties, clipping, padding,
endianness, packed nibble order, metadata schema, quantized/excluded tensor classes, calibration identity.
Dequantization математически определена и tested round-trip; tail groups не теряются.
Norm/gate/recurrent state не квантуются «за компанию». Precision policy отражается в model manifest.

## Converter

Source weights read-only; output отдельный каталог; потоковое чтение shard; bounded scratch; точный tensor accounting.
Ошибка или нехватка места оставляет incomplete output, не usable-looking model. Повторный запуск не перетирает
правильный checkpoint без явной опции/подтверждения. hashes до/после и metadata source revision обязательны.

## Training

Frozen quantized base должен давать правильный gradient к inputs и LoRA tensors. Не делать fake gradients
к integer packed weights. Fused quantized forward может иметь separate differentiable implementation для training,
но выбор пути visible и проходит model-level gradient tests.

## Quality gate

BF16 vs quant на одном fixed holdout, same input IDs/templates/sampling controls. Logits/NLL drift и behavior,
long-context recurrence, code/Russian sanity, image path если quant затрагивает vision. Calibration и evaluation разделены.
Любая обещанная экономия памяти должна включать scales/unquantized tensors/KV/workspaces, а не только bits/parameter.

## Extended formats

FP8/NVFP4/MXFP4 additions — последующие capability entries с собственными tests; не все обязательны для первого релиза.
Одного проверенного quant format достаточно, если выполняется product/API contract. `QTZ-05` — optional extension,
не повод задерживать хороший single-Spark release и не разрешение потерять первый quant gate.
