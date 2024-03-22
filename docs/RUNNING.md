# Run FeedSlicer

## Input folders

The Linux batch launcher `run_hungary_splits.py` accepts this study structure:

```text
Hungary_Organised/Fidesz/1/20240328/Instagram/recording.mp4
Hungary_Organised/Fidesz/1/20240328/TikTok/recording.mp4
```

| Level | Accepted value |
| --- | --- |
| Party | `Fidesz` or `Tisza` |
| Participant | `1`, `2`, `3` or `4` |
| Date | A valid calendar date in `YYYYMMDD` form |
| Platform | Instagram or TikTok, case-insensitive |
| File | A regular MP4 file; input symlinks are rejected |

These paths illustrate the folder format. Set `--input` to the dataset root;
`--scope Fidesz/1` selects the relative subtree. Input and output roots must be
separate and non-overlapping. Avoid `.mp4` within output directory names.

## Preserve the source recordings

The base processor deletes its input pathname after its final export. The
launcher supplies a private symbolic link named `input.mp4`, so this removes
the staging link. It redirects exports into a fresh run directory and closes
both OpenCV and MoviePy resources.

After each job it compares source device, inode, size and modification time.
This metadata check does not hash the recording contents.

## Preflight and processing

Install the [separate environment](ENVIRONMENT.md), then run from the repository
root. Replace the absolute paths below:

```bash
.venv/bin/python run_hungary_splits.py \
  --input /absolute/path/Hungary_Organised \
  --scope Fidesz/1 \
  --output /absolute/path/Hungary_Splits \
  --workers 4 \
  --check-only
```

Remove `--check-only` to process recordings. Preflight checks dependencies,
templates, folder structure, scope and available CPUs. It does not decode
every recording or establish that every export will succeed.

Always override the default input and output paths when moving to a different
CSC project or machine.

## Workers and cluster resources

The default is 32 workers. Start with a small allocation, such as the explicit
`--workers 4` example, and keep the count within the CPUs available to the
Linux process. The launcher uses spawned worker processes, assigns CPU affinity,
and limits several library thread settings.

Run inside the resources allocated by your cluster job. This launcher does not
submit a Slurm job or request resources itself. FFmpeg inherits worker affinity;
affinity limits scheduling, not the number of threads a library can create.

Each run gets a timestamped directory with a unique suffix, avoiding old output
paths that the shared exporter would otherwise skip.
