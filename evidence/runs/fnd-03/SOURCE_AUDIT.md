# FND-03 source audit

Candidate commit after first review remediation: `06222b0bcdc43ac8e775c5316ac4a6ddb22137a0`. Review state: pending.

## Immutable top-level revisions

- MLX: `365bd0fbac2e96631a1b2c4a34ca5a0771cdfde5`
- MLX-LM: `7fb4be44d560e5b74595210f83cb6003a57e52a7`
- Transformers oracle: `0df4ef369d324d4072e2910c673671eed4e92459`
- Qwen/Qwen3.8-27B: `1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0`

`configs/source-lock.resolved.json` records the exact-revision URLs, byte counts, and SHA-256 values for every
audited metadata/source file. It contains no executable `main`, `master`, or `latest` reference.

## Licenses and Qwen metadata

The exact MLX and MLX-LM notices contain the MIT grant and have identical SHA-256
`ccfab7ccb2ea306f71531c8ca77bb55507606cd90768b1e32b8b52ab5b48cf01`. The exact Transformers and Qwen
license files contain Apache License 2.0 notices. The Qwen model card and exact model API also declare
`apache-2.0`.

The exact Qwen config raw bytes hash to
`191e0af232104ed8b65258cf3fb2b842e288008baca7633c11b82a1ac7203aab`. Its parsed JSON is structurally equal
to `configs/models/qwen3.8-27b.config.snapshot.json`; both canonical JSON objects hash to
`137754ebd46991bec0c0d9e660dc98256be0b20f0e825b28c95c31de6142d041`. No changed path was observed.

The exact weight index hashes to `77042094076611b69791a610065f28b7013b8c621795fa86ddccc8bac7d1b9df` and maps 1199 tensors to
18 basename-only safetensors shards. Its `metadata.total_size` is 55,562,855,904 bytes. This is tensor payload,
not the on-disk file sum.

## Existing exact-revision weights on DGX2

The committed stdlib-only probe checked configured/standard Hugging Face cache roots and only the exact model and
snapshot path. It found config, tokenizer, tokenizer config, a parsed safetensors index, and 18/18 shards at the
locked revision. Their aggregate file size is 55,563,006,776 bytes (150,872 bytes above the index tensor-payload
value due to container/header overhead). The local config, index, and tokenizer-config SHA-256 values match the
audited exact-revision metadata; `all_exact_index_shards_present=true`. The probe emitted no paths, environment
values, user, hostname, or secrets.

No weight was downloaded, modified, opened as a model, or hashed end-to-end. The user authorized a download if
needed, but the exact snapshot was already complete, so a redundant transfer would add risk without evidence value.

## Oracle and CUDA constraints

Pinned Transformers contains the `qwen3_5` config and model source used by Qwen3.8, plus auto mappings for
conditional generation and multimodal processing. This is source-presence evidence only. Any future oracle must use
local/offline inputs, `USE_HUB_KERNELS=NO`, `use_kernels=False`, and `trust_remote_code=False`.

Pinned MLX requires CUDA Toolkit and cuDNN, rejects CUDA 13.1, selects the native architecture by default, appends
the accelerated suffix for architecture values >=90, and uses a CUDA-12.8-gated compression flag. GB10 `121a` is
therefore only an inference from source and FND-02 inventory; it has not been accepted by nvcc or exercised.

The exact commits behind seven direct CMake source declarations are recorded. The selected upstream CMake still
names tags/archives without content hashes, so the lock has `networked_build_allowed=false`. FND-04 must materialize
or override those exact dependency revisions before any networked build. No claim of reproducible build is made.

## Protected boundary

No build, install, source import, model load, CUDA execution, system change, second-node access, TP2, or NCCL work
was performed. FND-03 does not turn the scaffold into a native framework and does not narrow the product goal of a
complete standalone MLX-like framework.
