# API, совместимость и запрет fake completeness

## Два разных утверждения

«Похожий удобный API» — дизайнерская цель. «Полная альтернатива MLX» — проверяемый coverage/semantics контракт.
Первый release должен перечислять exact reference commit, imported source commit, каждую применимую публичную функцию,
класс, transform и метод, а также hardware-specific equivalents/exclusions. [S03,S08]

`planning/API_PARITY_SEED.csv` — стартовый список семейств/представителей. Он намеренно не называется полным inventory.
FND-07 получает полный список из pinned API/source в isolated environment, включая array methods, random, linalg,
fft, fast, device/stream, export/load, nn и optimizers. Для Python динамического surface одного grep недостаточно.

## Таблица статусов

`not_started`: нет product implementation. `implemented_unvalidated`: код есть, evidence нет.
`reference_tested`: только mathematical/CPU reference. `hardware_validated`: real GB10 tests в recorded configuration.
`equivalent_cuda`: аппаратно-специфичный Metal API заменён объявленным CUDA-equivalent.
`deferred_by_owner`: только distributed/TP2 и другие явно отложенные платформы. `not_applicable`: строго обоснованная
platform binding, не неудобная математическая операция. `release_ready`: все применимые уровни закрыты.

## Семантическая совместимость

Проверять подпись, defaults, return trees, dtype promotion, zero/empty behavior, errors, broadcasting/indexing,
random state, differentiation, streams и serialization. Namespace migration `mlx`→`mlx_spark` описывается явно:
пакет не обещает drop-in импорт `mlx` и не перезаписывает чужую установку.

## Шаблон пользовательского опыта (пока DESIGN)

```python
import mlx_spark.core as mx
import mlx_spark.nn as nn
import mlx_spark.optimizers as optim

# После реализации native core, не в текущем scaffold:
# loss_and_grad = mx.compile(mx.value_and_grad(loss_fn))
# loss, grads = loss_and_grad(parameters, batch)
# optimizer.update(model, grads)
# mx.eval(model.parameters(), optimizer.state)
```

Этот snippet не acceptance test, пока функции не реализованы. Пример с `lambda f: f` вместо compile запрещён.
`mx.grad` не может считать конечные разности как скрытый production autodiff. `vmap` не должен быть
маркетинговым названием последовательного Python loop без оговорки experimental/reference status.

## Общие workload-тесты

Linear regression и MLP, convolutional toy, recurrent differentiable toy, masked attention toy,
complex/FFT и linalg numerical suite, user-defined primitive extension. Это не выбор новых больших моделей,
а проверка обещания general framework. Qwen-only operator coverage не закрывает API gate.

## C++ и дополнительные binding языки

C++ API/SDK с documented headers/link targets является single-Spark release requirement.
C/DLPack interop поддерживается осмысленно; отдельные C/Swift bindings оцениваются в exact parity inventory,
а не молча объявляются готовыми. macOS/Metal/Swift UI не нужен для Linux Spark release; math semantics остаётся общим.
