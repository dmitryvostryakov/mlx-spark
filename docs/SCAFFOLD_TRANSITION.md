# Как превратить scaffold в продукт, не уничтожив честные проверки

Текущие core/nn/optimizers deliberately unavailable. CLI status возвращает scaffold_only.
После настоящей FND-06 реализации эти статусы должны выводиться из build/capability manifest,
а не навсегда оставаться false или безусловно заменяться на true.

Тест `test_missing_native_fails_not_fallback` сейчас утверждает исходное состояние bundle. Когда появится проверенный
native extension, заменить его двухветвевым тестом: isolated env без extension честно fails; installed product env
реально исполняет операцию и не импортирует hidden backends. Это legitimate test evolution с implementation evidence,
не удаление test ради green. Аналогично strict source-null fixture остаётся тестом candidate artifact, а real resolved
lock получает отдельные checks.

Существующие математические references не становятся implementation: они сохраняются как independent oracle и могут
быть вынесены в test-only package. Новые framework tests должны импортировать `mlx_spark`, проверять dtype/device,
backend manifest и реальные gradients. Их нельзя удовлетворить NumPy fixture.

C++ host library — contracts scaffold. CUDA reference kernel — preliminary correctness artifact. Importing upstream
в checked-in tree, самостоятельный `_core`, binding migration и полноценный runtime остаются задачами FND/CORE/AD/MEM/EXEC.
Не путать CMake host success с компиляцией всего MLX-Spark.
