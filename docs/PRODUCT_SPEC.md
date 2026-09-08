# Спецификация продукта

## Миссия

Дать разработчику на DGX Spark целостную среду разработки ML: от массива и производной до обучения,
квантования и локального исполнения моделей. Qwen3.8-27B — первый большой acceptance workload,
а не перечень разрешённых архитектур. Новая пользовательская сеть должна работать без патча ядра.

## Полная альтернатива: проверяемое значение

Полнота определяется относительно зафиксированной публичной поверхности MLX, а не рекламного описания.
Обязательны array semantics, math/linear algebra/FFT, CPU/CUDA execution, lazy materialization, function transforms,
компиляция, modules/losses/optimizers, serialization, interoperability, memory diagnostics и usable Python/C++ SDK.
У MLX действительно есть соответствующие семейства API; точный inventory извлекается в FND-07. [S03,S08]

Кандидат `planning/API_PARITY_SEED.csv` — только seed checklist. Количество строк не равно количеству поддержанных символов.
Каждый реальный symbol из pinned reference должен получить semantic status, backend status и test evidence.
Платформенно специфичный Metal API не копируется фиктивно: его операция получает CUDA-эквивалент либо explicit platform exclusion.
Distributed APIs обозначены `deferred_by_owner_to_phase2`, а не `implemented` и не скрываются из общей карты.

## Apple-like требования

Единый понятный import/API, предсказуемые типы и исключения, хорошая установка и documentation, правильные defaults.
Пользователь не должен разбираться с несовместимыми конвертерами ради обычной операции, но runtime не скрывает
CPU fallback, math mode, изменение точности или реальные ограничения памяти. Error message отвечает: что не получилось,
что было запрошено, сколько нужно/доступно, какой безопасный следующий шаг.

Установка готового релиза — собственный tested ARM64 wheel/SDK в совместимой среде. Проект не устанавливает драйвер
за пользователя и не выдаёт набор packages с плавающими версиями за one-command production experience.
GUI, web-server и кластерная панель не обязательны: Apple-like здесь означает качество framework, а не копирование оболочки macOS.

## Приёмка одного Spark

Публичный API general-purpose; arbitrary toy training и transforms; Qwen text BF16, корректный session state,
проверенные LoRA/QLoRA и quantization, vision/video и MTP по отдельным gate, но до полного model-support release.
Text-only alpha допустима как промежуточный milestone и явно так называется. TP2 не открывается после alpha.
Полное обучение 27B всех параметров не обещается при невозможном memory budget: при этом full training API на небольших
сетях и честные поддержанные большой моделью режимы обязательны.

## Самостоятельность

Допускается reuse MIT source с notices. Готовый продукт имеет собственные binary artifacts, namespace, releases,
dependency graph, tests и support contract. Не требует установленного MLX или PyTorch для обычной работы.
Baseline PyTorch/Transformers/MLX живёт в отдельном oracle env. Не надо переписывать математическую библиотеку
из идеологических соображений; надо исключить подмену самостоятельного framework внешним сервисом.

## Границы первой фазы

Один выбранный DGX Spark / одна GPU GB10. Второй узел не участвует даже в обязательных тестах.
Не добавлять NCCL dependency, network transport, SSH launcher, TP/PP/EP, других больших моделей или обслуживающих приложений.
В ядре сохраняются нормальные границы primitive/model/serialization, достаточные для последующего TP2 без реализации распределённости.

## Название и лицензия

`MLX-Spark` — рабочее имя. Проверка имени пакета/товарного обозначения до публикации — отдельный release вопрос.
Выбор лицензии нового кода остаётся за владельцем; не приписывать проект Apple/NVIDIA endorsement.
Исходные MIT/Apache и прочие notices сохраняются согласно audited imported components. [S09]
