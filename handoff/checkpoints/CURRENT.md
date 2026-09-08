# Checkpoint

Timestamp UTC: 2026-09-08T08:54:22Z
Role / task / reviewed state: Sol / FND-02 / `7b0c1421b33c8606db77f68a2aa035c298260539`

## Цель текущего участка

Получить честную read-only инвентаризацию выбранного DGX2 и безопасные resource budgets, сохраняя целью
полноценный самостоятельный framework.

## Защищённый scope

Только DGX2 как один выбранный Spark и одна его GPU. Никаких запросов ко второму узлу, network scan, stress,
install/system/service changes. TP2/NCCL/QSFP остаются закрыты до принятого стабильного single-Spark release.

## Уже сделано и доказано

- FND-01 принят; base integration commit `c29d9d918dc473bca9b5cf055880e950e064a2f5`.
- FND-02 claimed для DGX2 и имеет статус `in_progress`.
- Contract-first реализован anonymized doctor для architecture/OS/DGX OS, memory/current cgroup hierarchy,
  selected filesystem disk, structured GPU/driver, nvcc, compiler, CMake и cuDNN.
- Doctor standalone и stdlib-only: его можно передать через stdin без remote install или file write.
- Два independent review pass запросили DGX OS, nested/hybrid cgroup и suppression raw version output. Final
  implementation re-review approved commit `624eb88bc5c31a628cbc15180db21ec5b6dbd3da`; hardware review не готов.
- Targeted doctor tests: 11/11 passed. Actual-evidence tests: 4/4. Full scaffold: 64 Python + 1 C++ passed.
  Raw logs: `evidence/runs/fnd-02/`.
- Owner-provided `ssh dgx2` подключился; standalone doctor выполнен через stdin с exit 0 без remote write/install.
- Observed: Linux aarch64, DGX Spark 7.2.3/OTA 7.5.0, Ubuntu 24.04.4, одна GB10/sm_121, driver 580.159.03,
  MemAvailable 113.51 GiB, no finite cgroup limit, no swap, selected-filesystem free 582.45 GiB.
- GCC 13.3.0 и CMake 3.28.3 доступны; nvcc unavailable, cuDNN unknown — compatibility не заявлена.
- Proposed budget: 80 GiB working set + 32 GiB reserve; 256 GiB project disk + 256 GiB free floor;
  96 GiB build cache; 4 build jobs; weights download не разрешён.
- Hardware facts/budget arithmetic accepted in first evidence review; replayable validation and stronger boundary
  tests added for requested evidence-fidelity remediation. Two independent re-reviews approved with no findings.
- Второй узел, сеть, CUDA workload, Qwen и TP2 не трогались.

## Сделано, но не проверено

Факты inventory получены на DGX2, но CUDA compile/runtime, allocation semantics и toolchain compatibility не проверены.
Никакой model/Qwen/training workload не запускался.

## Блокировки и точные входные данные

CUDA toolkit version остаётся unknown из-за отсутствия `nvcc` в PATH; cuDNN version не найден. Это не блокирует
честное завершение inventory при явных unknown, но будет входом для source/build compatibility следующих задач.

## Решения / ADR

Нового архитектурного ADR нет. JSON не содержит hostname/IP/MAC/UUID/serial/user/home/mount/env/interfaces/processes.
Version strings будут только inventory facts, а не доказательством CUDA compatibility.

## Next 1–3 tasks

1. Проверить DAG: единственная следующая Sol-задача должна быть FND-03.
2. Claim FND-03 только с explicit network opt-in для metadata resolution.
3. FND-04 после FND-03; TP2 не трогать.

## Рабочее дерево

FND-02 approved state и status updates сохранены integration commit
`d993e0a2d9da281eda86cc8dd9b0494d1197e21a`; после pointer-only checkpoint update дерево должно быть clean.
