# Сборка, pinning и безопасность цепочки поставки

## Что известно и что ещё нет

Наблюдавшийся MLX source candidate — полный SHA из upstream commit page [S04]. Code поддерживает CUDA,
но опубликованный main может содержать ограничения toolkit. Например, просмотренный CMake явно отвергает CUDA 13.1 [S13].
Это свойство просмотренной версии, а не закон для любого MLX/Spark. Не выбирать «самую свежую CUDA» автоматически.
Документация установки и main source могут отличаться по версии; решение принимает audited pinned source+real build. [S08]

Target Python minor, ABI, CUDA toolkit, driver, cuDNN, cuBLAS/cuSolver, host compiler, CMake, BLAS/LAPACK,
C++ standard, glibc, SM targets и native dependencies фиксируются после read-only inventory.
Документационный target GB10 sm_121 подтверждён NVIDIA [S07]; `nvcc` обязан реально поддержать выбранную target architecture.

## Две среды

**Oracle/baseline:** pinned unchanged MLX CUDA и independently pinned PyTorch/Transformers.
**Product:** собственный source tree/namespace/native binary без installed mlx/torch dependency.
Не ставить обе версии в system Python. Никакого автоматического обновления уже существующих venv/service containers.

## От candidate к lock

1. Прочитать candidate JSON; null — unresolved, не fake SHA.
2. Явно выполнить metadata-only `resolve_sources.py --allow-network` в новый output file.
3. Review SHA/date/license/compatibility, source diff и config snapshot diff; заполнить review evidence.
4. Только approved lock позволяет materialize исходники через `fetch_upstream.py`.
5. Загрузка больших weights — отдельный механизм после disk/memory budget; bootstrap этого не делает.

FND-03 фиксирует также exact commit SHA прямых CMake source dependencies, обнаруженных в выбранном MLX source.
Сам upstream CMake при этом всё ещё использует tags и архивы без content hash. Поэтому approved top-level source lock
разрешает materialize MLX source, но не разрешает сетевой CMake build: FND-04 должен сначала предоставить exact
dependency sources/overrides и сохранить их hashes. Наличие pin в audit не переписывает upstream CMake автоматически.

Scripts не требуют токенов для публичных metadata, не печатают env и не исполняют remote model code.
Source discovery через сеть не подтверждает безопасность/качество исходного проекта; проверяется точное выбранное состояние.
Полностью vendored MLX не включён в ZIP, потому что в среде подготовки не был загружен и аудирован полный исходный tree.

Transformers oracle для Qwen3.8 использует встроенный `qwen3_5` contract. Он запускается только offline/local с
`USE_HUB_KERNELS=NO`, `use_kernels=False`, `trust_remote_code=False`; source presence не считается runtime validation.

## Компиляция

Host scaffold command `cmake --preset host-debug` не собирает MLX и не означает CUDA support.
Opt-in `spark-cuda-candidate` компилирует только probe и reference toy kernel. Это отдельный preliminary hardware task.
Upstream baseline build recipe создаётся из конкретных CMakeLists в FND-04; не копировать flags из устаревших статей.
Не зашивать неподтверждённые cuDNN/CUTLASS/CUDA версии в production manifest ради видимости lock.

## Release builds

Две clean builds с одинаковым lock; compare generated binaries/metadata с учётом нормализованных nondeterministic полей.
Generate SBOM/license notices, binary dependency scan (readelf/ldd with care), RPATH audit, import namespace audit,
wheel install/uninstall и C++ consumer example. Ни runtime code download, ни JIT compile remote text по умолчанию не допустимы.
Custom user kernels — явная локальная функция с documented trust boundary.

## CI

В ZIP есть минимальный **template** GitHub Actions только CPU scaffold. Tag refs actions ещё нужно заменить reviewed SHA
до production use. Приватный Spark runner не запускает fork PR/untrusted code. Hardware jobs — manual/trusted branch,
без secrets в stdout и без concurrent benchmarks. Установка self-hosted runner сейчас не выполняется.

## Лицензии и публикация

MLX source MIT; model repo обозначает Apache-2.0 [S09,S02]. Не копировать один общий LICENSE на все зависимости.
Новый код/бренд/публикация — решение владельца; hand-off не создаёт repo/remotes и не публикует пакеты.
Большие weights, vendor toolkits, credentials и hardware identifiers не входят в deliverable ZIP.
