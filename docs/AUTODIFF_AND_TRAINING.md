# Autodiff и обучение — штатная часть ядра

## Непереговорные требования

Reverse-mode VJP, forward-mode JVP, vmap, higher-order и композиция с compile/lazy semantics.
Градиенты through stateful pure functions, parameter trees, shared weights и checkpointed activations.
MLX function transforms композиционны по публичному замыслу; альтернатива должна сохранять это свойство [S12].

## Проверка в правильном порядке

Small scalar/matrix analytic tests → finite differences на float64/float32 → broadcasting/indexing/conv
→ grad composition → generic MLP/recurrent training → конкретная большая Qwen LoRA.
У numerical oracle другой precision допустим; сравнение должно учитывать conditioning и approved tolerance.
Finite difference не заменяет production differentiation. Matching one scalar loss недостаточно.

## Transform matrix

Для каждого primitive отметить forward/VJP/JVP/vmap/higher-order/compiled/CPU/CUDA.
Без поддержанного fast path возможен explicit differentiable composed path на том же backend;
невозможность gradient должна дать exception, а не stop-gradient или zeros без просьбы пользователя.
Отдельно тестировать compiled forward против eager, compiled grad против eager grad и RNG/checkpoint interactions.

## GDN state

State output участвует в backward, если train graph продолжается через следующие chunks.
Full BPTT сохраняет gradient across chunk boundary. Explicit truncated-BPTT — отдельная настройка и документированный
tradeoff. Inference KV/cache оптимизации не должны случайно определять training detach policy.
Backward для gated recurrence сверять с bundled analytic VJP и независимым source oracle.

## Generic training acceptance

Через реальный публичный `mlx_spark` обучить synthetic linear/MLP, conv и recurrence model.
Проверить gradient checks, loss improvement, mode switching, parameter freeze, tied parameters,
optimizer state restore, accumulation и checkpoint resume. Численные результаты baseline заранее фиксируются.
Reference `analytic_sgd` в bundle только fixture для внешнего сравнения: он не использует autograd и не закрывает этот gate.

## Qwen LoRA/QLoRA

Explicit target modules/rank/alpha/dropout и base revision. Первым BF16 frozen base.
Gradients через слои recurrence сохраняются до adapter parameters; freeze не означает detach input.
QLoRA после verified quantized input-gradient. Каждый quantized tensor/adapter имеет dtype и packing manifest.
Проверить frozen base hashes до/после, adapter save/reload, merge (если поддерживается), и reference equivalence merge/unmerged.

## Reproducibility

Checkpoint: parameters/adapters, optimizer moments, scheduler, RNG/key, accumulation step,
scaler если применён, iterator/dataset position, train/eval mode, model/config/quant revision.
Exact resume ожидается в том же declared deterministic environment; межbackend bitwise equality не обещать без оснований.
Сохранять atomic + manifest marker только после successful flush; не писать в оригинальный checkpoint.

## Данные и качество

В scaffold используются синтетические локальные fixtures. Большие данные/приватные prompts/медицинские материалы не нужны.
До real fine-tuning отдельный license/consent/data minimization audit. Train loss не равен полезности после обучения:
held-out sanity и degradation checks обязательны. Нельзя одновременно настраивать quantization на holdout и заявлять unbiased quality.
