# Verification

## Source and asset integrity

```bash
python3 tools/verify_sources.py
```

This checks SHA-256 values for 18 source, template, notebook and reference
files against `SOURCE_MANIFEST.json`, without importing or executing processors.

| Check | Scope |
| --- | --- |
| Source bytes | All 18 files match the recorded hashes |
| Python syntax | The seven processing and entry-point files parse without execution |
| Notebook structure | The three notebooks parse as JSON; cells are not executed |
| Template files | All six PNGs decode at their original dimensions |
| Workflow diagram | LaTeX compiles to one PDF page; rendered layout is visually checked |

## Runtime evidence

The pipeline has not been rerun as part of this repository review. The available
sample MP4 failed FFprobe with `moov atom not found`, so it is not used as a
demonstration asset. The requirements are a compatibility recipe, not an
end-to-end-tested environment or a full lockfile.

Recorded notebook outcomes are described in [EVIDENCE.md](EVIDENCE.md).
Boundary accuracy, output coverage, timestamp fidelity and parallel throughput
remain unmeasured here. Operational status is not a measurement of scientific accuracy.
