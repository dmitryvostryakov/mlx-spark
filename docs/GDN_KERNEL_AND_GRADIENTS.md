# Gated DeltaNet: точная граница primitive и стратегия CUDA

## Референсный контракт

Bundled oracle `reference/gdn.py` получает уже нормализованные/scaled q,k, values v,
**мультипликативное** затухание g, beta и state. Shapes:
q,k `[B,T,Hk,Dk]`; v `[B,T,Hv,Dv]`; g,beta `[B,T,Hv]`; state `[B,Hv,Dv,Dk]`.
`Hv/Hk` целое, value-head h использует key-head floor(h/(Hv/Hk)). Mask `[B,T]` bool.
Этот контур согласуется с просмотренным scalar-gate MLX-LM path; source ещё нужно закрепить immutable lock [S10].

## Математика одного шага

Для одного value head и value row (matrix form для всех rows):

```
P_t = g_t * S_(t-1)
r_t = v_t - P_t @ k_t
d_t = beta_t * r_t
S_t = P_t + outer(d_t, k_t)
y_t = S_t @ q_t
```

Masked step выдаёт zero output и сохраняет S_(t-1). State input не модифицируется oracle.
Если target implementation использует log-decay, он конвертирует его в g в явном месте; нельзя смешивать conventions.
q readout scale не вставлять повторно в primitive. GDN в модели также включает нормализацию, convolution,
learned gating и projection, которые этот отдельный oracle **не** реализует.

## Обратный проход

При incoming dS, dy: добавить outer(dy,q) к dS; dq=S_t^T dy.
Для delta/update d_delta=dS @ k; dk+=dS^T delta; dP начинает с dS.
Для residual dv=beta*d_delta; dbeta=sum(d_delta*r); dr=-beta*d_delta;
dP+=outer(dr,k); dk+=P^T dr. Затем dg=sum(dP*S_prev); dS_prev=g*dP.
Суммировать q/k cotangents по повторённым value-head groups. Masked paths дают нулевые input gradients
и identity cotangent для state. Это реализовано в original analytic NumPy VJP и проверяется конечными разностями.
Это не замена настоящего autograd framework; это его независимый test oracle.

## Bundled CUDA candidate

FP32, T=1, scalar gates, contiguous buffers, Dk∈{32,64,128,256}. Один block на (B,Hv,Dv row),
shared-memory reductions. Цель — простой correctness baseline. Он не интегрирован в lazy graph/autograd,
не заявляет оптимальность, не поддерживает BF16/vector gates/strides и не тестировался на GPU при подготовке.
Device pointer ownership/size — caller contract. Любая aliasing optimization требует нового tested contract.
Сначала compile и compute-sanitizer memcheck/racecheck на одном GB10; затем randomized/edge cases.

## Production sequence

1. Подтвердить FP32 baseline и independent formula на small shapes.
2. BF16 inputs/output при FP32 state/accumulation; long recurrence drift tests.
3. Decode optimization: shared reduction/shuffle/vectorization только после profile occupancy/register pressure.
4. Chunked prefill: иной алгоритм с ограниченным workspace; serial loop остаётся oracle.
5. Backward/recompute: bounded activation memory, full BPTT contract; explicit truncation отдельно.
6. JVP/vmap/higher-order support или видимый differentiable generic path, не silent detach.

## Shapes для acceptance

B 1/2/4, T 0/1/2/7/16/127/128/129 и большие prefill по бюджету, Hk/Hv grouped,
Dk 32/64/128/tail unsupported, Dv odd и production128; zero/nonzero initial state;
all/partial/no mask; g близко к 0/1; beta близко к0/1; negative/large values; tail chunks.
Unsupported shape обязан fail или выбрать declared correct fallback. Включить fast-math policy и compiler flags в evidence.

## Чего не обещаем

48 из 64 слоёв не означает 75% runtime. Микробенчмарк не предсказывает end-to-end скорость.
MLX issue про MoE gather_qmm не относится к dense Qwen3.8-27B priority. Решение о первом production fast path — по нашему profile.
