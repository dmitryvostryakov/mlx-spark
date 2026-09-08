# Независимая review

## Scope
Полный framework не подменён wrapper? Один Spark? Новые сетевые/distributed зависимости отсутствуют?
API changes согласованы? License notices сохранены? Нет private data/system edits?

## Semantics
Shapes/dtypes/layouts/tails/empty/masks учтены? q scaling и norm conventions один раз?
State update/rollback/cache lifecycle корректны? Backward/JVP/vmap не silently detached?
Compiled/eager, train/eval и save/resume согласуются?

## Safety
Allocation overflow/bounds, streams lifetime, source checkpoint overwrite, failed save, malformed input,
OOM recovery и cancellation проверены? Unsupported paths explicit? Thread ownership/async errors безопасны?

## Evidence
Тест действительно запускает новую implementation? Нет mock/fallback/skip вместо native?
Raw commands/results доступны? Compare same revision/precision/context? Tolerances preregistered?
Reported throughput measured with correct synchronization? GPU identity/environment действительно наблюдались?

## Decision
Approve / changes requested / blocked. Конкретные gaps, не общая фраза. Reviewer не implementer для release signoff.
После approve — integration smoke/regression в общем tree и update task/context.
