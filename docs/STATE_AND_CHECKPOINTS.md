# State, lifecycle, snapshot и checkpoints

## Два типа состояния

**Сессия inference:** attention KV, GDN recurrent state, convolution history, positions, tokenizer/context identity,
RNG/sampling metadata, optional vision context и MTP draft/verification state.
**Training checkpoint:** параметры/буферы, optimizer/scheduler/RNG, dataset position, accumulation/scaler и version manifests.
Не смешивать transient GPU addresses и persistent semantic identifiers.

## Идентификатор совместимости

Model revision + config hash + quantization map hash + state schema version + relevant positional/sampling configuration.
Session cache нельзя молча использовать после смены weights, template или несовместимой math policy.
В первой версии не обещаем переносимость cache между backend/versions. Restart from token history — отдельная безопасная возможность.

## Immutable semantic snapshot

Исходный контракт: fork создаёт независимое consistent state. Реальная implementation может использовать
copy-on-write/refcount/slices только при доказанных lifecycle/alias guarantees и одинаковой семантике.
Bundled ReferenceSnapshot deep-copies CPU arrays, проверяет базовый invariant; это не производительный KV allocator.

## Chunking и rollback

После обработки любого префикса дальнейшее продолжение должно согласовываться с whole-prefix baseline.
Mask и padding semantics одинаковы для KV, conv, recurrence и positions. KV trim не откатывает recurrent update.
MTP rollback требует snapshot/replay или другого проверенного алгоритма для всего state, включая RNG counters.
Отмена generation должна освобождать собственные временные allocations, не нарушая другие live arrays.

## Save/load

Versioned manifest, dtype/layout names, shape checks, total sizes и hashes. Atomic temporary output + fsync/rename
с marker завершения; не писать в source checkpoint, особенно если он lazily mapped. Large tensors safetensors/выбранный
non-executable format; pickle и remote code не default. Прерванная запись не читается как полноценный checkpoint.

## Acceptance fixtures

Whole/chunk boundaries 1,2,3,7,128; repeated branch/restore; nonzero initial state; generation A/B isolation;
random cancellation offsets; model reload; corrupt/truncated checkpoint; wrong revision; training split/resume.
Structured state tensors должны сравниваться до decoded outputs — иначе нет локализации ошибки.
