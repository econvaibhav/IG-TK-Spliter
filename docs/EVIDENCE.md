# Recorded runs and diagnostics

## Batch run

`archive/notebooks/test.ipynb` contains a saved run dated 20 September 2026:

| Recordings | `ok` | `needs_review` | `failed` |
| --- | --- | --- | --- |
| 48 | 40 | 1 | 7 |

These are recorded operational outcomes. They do not measure segmentation
accuracy, and the notebook is not a fresh benchmark run.

## Export diagnostic

`archive/notebooks/ffmpeg_diagnostics.ipynb` records `pts/dts pair unsupported`
for one MP4 export. Adding `video_track_timescale=90000` made one 30-second
diagnostic export succeed. The processor does not include this option. The
result does not establish the cause of every failed job or a general repair.

## Notebook use

`Run_in_Roihu.ipynb` wraps the batch launcher and assumes its original CPU and
interpreter configuration. The exploratory notebooks include real study paths,
dependency changes and recovery commands. Read relevant cells before executing
them; use the current running guide for setup.

The tests described in `archive/roihu/README.original.md` are historical records.
They are not checks rerun by the repository documentation.
