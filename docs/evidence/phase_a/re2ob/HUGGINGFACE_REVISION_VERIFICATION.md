# Hugging Face Dataset Revision Verification

Date: 2026-10-03
Dataset repository: `phamquiluan/RCAEval`
Pinned revision: `afeacb11bcc94dadfd1c8f483ee4377b2b8b614e`

## Independent upstream verification

The exact pinned revision resolves on the Hugging Face dataset repository. The
upstream commit page identifies commit `afeacb1` as verified, with subject
`Document case index; enable viewer`; the tree view at the exact full revision
also resolves successfully.

Upstream commit URL:
`https://huggingface.co/datasets/phamquiluan/RCAEval/commit/afeacb11bcc94dadfd1c8f483ee4377b2b8b614e`

Upstream tree URL:
`https://huggingface.co/datasets/phamquiluan/RCAEval/tree/afeacb11bcc94dadfd1c8f483ee4377b2b8b614e`

No RE2-SS/RE2-TT raw case directory was opened for this verification.

## Local metadata reconciliation

Local root:
`/home/dell/datasets/rcaeval/afeacb11bcc94dadfd1c8f483ee4377b2b8b614e`

- metadata files inspected: 361
- first-line revision equal to the pinned full hash: 361/361
- nonmatching revision records: 0
- empty metadata records: 0
- `cases.parquet`: present
- RE2-OB raw case directories: 90
- RE2-SS raw case directories: 0
- RE2-TT raw case directories: 0

Example proof file:
`.cache/huggingface/download/re2ob_checkoutservice_cpu_1/metrics.parquet.metadata`
Its first line is the exact full pinned revision.

The dataset-revision portion of Phase A Step 2 is therefore **VERIFIED**, not
merely locally supported. This does not independently validate every file's
content hash against upstream; it verifies the requested revision identity and
the provenance recorded by the local Hugging Face downloader metadata.
