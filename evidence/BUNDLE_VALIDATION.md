# Отчёт проверки доставляемого пакета

Дата: **2026-09-08**. Объект: engineering hand-off/scaffolding, **не готовый MLX-Spark framework**.

## Реально выполнено

| Проверка | Результат | Evidence |
|---|---|---|
| Python/reference suite | **47 passed**, без пропущенных тестов | `validation/pytest.txt` |
| C++20 host contracts | Сборка успешна; **1/1 CTest passed** | `validation/cmake-configure.txt`, `cmake-build.txt`, `ctest.txt` |
| Граф задач | **91 задача**, 85 single-Spark + 6 deferred TP2; циклов нет | `validation/plan.txt` |
| Python, JSON, TOML | Синтаксическая проверка; проверка коллизий имён файлов без учёта регистра | `validation/content-checks.json` |
| Сборка Python wheel | Offline, no-deps, без build isolation | `validation/wheel-build.txt` |
| Установка wheel в новый venv | Успешна, без сети и зависимостей | `validation/wheel-install-clean.txt` |
| Изоляция установленного каркаса | В окружении нет `mlx`, `torch`, `numpy`; status работает | `validation/wheel-isolation.txt`, `wheel-status-clean.json` |
| Отсутствующее native core | `mx.array` явно выдаёт `NativeCoreUnavailable` | `validation/wheel-isolation.txt` |
| Release checker | Незавершённый TEMPLATE отклонён с exit 2 | `validation/expected-gate-rejection.json` |
| HTML / ссылки | Проверены локальные пути, уникальность IDs; нет внешних ресурсов для отображения | `validation/content-checks.json` |
| HTML в браузере | Chromium: desktop/mobile, поиск, раскрытие документов; JS-ошибок и общего горизонтального переполнения нет | `validation/html-browser-check.json` |
| Manifest | SHA-256 каждого доставленного файла; проверяемый `tools/check_integrity.py` | Корневой `MANIFEST.sha256` |

Численные проверки включают GDN forward, analytic VJP против конечных разностей, grouped heads, chunking,
маски и неизменность состояния. Отдельно проверены причинное GQA attention, snapshot isolation и toy SGD/resume.
Это независимые CPU-эталоны, **не реализация production autograd и не доказательство корректности Qwen целиком**.

Wheel называется `mlx-spark-scaffold` и устанавливает namespace `mlx_spark`.
Проверка packaging относится только к Python-scaffold: она не доказывает готовность ARM64/native CUDA wheel.
Собранные локальные бинарники и wheel не входят в ZIP; исходники и журналы проверки входят.

## Что НЕ проверено и НЕ заявляется

- Доступ к принадлежащим владельцу Spark, DGX OS/driver/CUDA/cuDNN на них.
- Компиляция/запуск CUDA probe, GDN candidate, CUDA sanitizers и аппаратная стабильность.
- Сборка полного upstream MLX либо собственного production native `_core`.
- Exact immutable HF revision и полный состав скачанных весов: веса не скачивались.
- Qwen text/vision/MTP inference, model-level numerical parity и длинный контекст.
- Обучение через настоящий framework, LoRA/QLoRA на Spark, quantization quality.
- Скорость, пиковая память модели, энергопотребление или преимущество перед другими движками.
- TP=2, сеть, второй узел, NCCL или QSFP. Эта фаза закрыта.

В delivery status все соответствующие флаги остаются `false` / `not implemented` / `deferred`.
Источник model config — нормализованный snapshot публичных фактов с отдельной provenance-записью;
он не выдаётся за оригинальный файл из закреплённого HF commit.

## Воспроизведение на своей машине

Из корня пакета, при уже установленных Python/NumPy/pytest/CMake/C++:

```bash
python3 tools/check_integrity.py
bash scripts/check_local.sh
python3 tools/next_task.py --agent Sol
```

`check_local.sh` не обращается к сети и не запускает CUDA. Для отсутствующих dev-зависимостей имеется
отдельный `scripts/bootstrap_dev.sh --allow-network`; он создаёт только новую локальную venv.
Проверки конкретного Spark выполняются в FND-02 на **одном выбранном узле**.

## Целостность и границы доверия

`MANIFEST.sha256` — контроль повреждения файлов, не криптографическая подпись автора.
Итоговый ZIP имеет внешнюю контрольную сумму, публикуемую рядом с архивом; manifest включён внутрь ZIP.
После намеренных изменений manifest доставки ожидаемо перестаёт совпадать; разработку продолжать под Git,
а не пытаться скрыть diff от проверяющего агента.

При FND-01 исходный JUnit XML был удалён из текущего дерева: даже generic `hostname` metadata нарушает строгий
запрет `AGENTS.md`. Его исходные байты остаются воспроизводимо доступны в сохранённом ZIP/base commit; текстовый
raw-отчёт `validation/pytest.txt` остаётся в текущем evidence. Исторический `validation/run-record.json` не
переписывался и поэтому по-прежнему фиксирует первоначальную команду генерации XML.

## Организация репозитория

47 основных документов/hand-off/ADR встроены в HTML-навигатор плюс 91 отдельная task card.
Task statuses описывают **будущую реализацию продукта**: ни одна продуктовая задача не считается завершённой
лишь потому, что локальный scaffold suite зелёный. Отдельно отслеживаются evidence, reviewer и acceptance.
