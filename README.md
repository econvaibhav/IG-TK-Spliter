# FeedSlicer

**Split Instagram and TikTok screen recordings into candidate post-level clips.**

FeedSlicer uses on-screen interface cues to find possible transitions between
feed items. OpenCV checks icon positions and feed geometry; FFmpeg exports
the intervals from the recording.

## How it works

| Step | Behavior |
| --- | --- |
| Frame processing | Reads frames individually and resizes the analysis image to 960 pixels high. |
| Instagram | Checks heart, comment and share positions, plus a separate four-corner feed-layout rule. |
| TikTok | Checks heart, share and save positions using platform-specific thresholds. |
| Export | Writes numbered MP4 clips from the original recording, with AAC audio. |
| Batch processing | Discovers recordings, runs parallel workers and writes per-video logs and a CSV summary. |

The platform comes from the folder path. Instagram runs both checks on each
frame. Icon rules require more than 0.4 seconds since the last cut; the
Instagram layout rule requires more than 1 second. These are interface
heuristics, so exported clips should be reviewed before analysis.

## Quick start

Use Linux, a separate Python 3.10-3.12 environment, and FFmpeg on `PATH`.
Run these commands from the repository root:

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
ffmpeg -version
```

The batch launcher expects `Party/Participant/YYYYMMDD/Platform/video.mp4`,
for example `Fidesz/1/20240328/Instagram/recording.mp4`. It accepts Fidesz or
Tisza, participants 1-4, and Instagram or TikTok folders.

```bash
.venv/bin/python run_hungary_splits.py \
  --input /absolute/path/Hungary_Organised \
  --scope Fidesz/1 \
  --output /absolute/path/Hungary_Splits \
  --workers 4 \
  --check-only
```

Replace the paths, run preflight, then remove `--check-only` to start processing.
Keep input and output roots separate. Use the launcher to preserve originals:
the base processor deletes its input pathname after export, while the launcher
passes a private symbolic link. See [running instructions](docs/RUNNING.md).

## Outputs

Each run creates a fresh directory with numbered MP4 clips, `summary.csv`,
per-video logs and `run_config.json`. The folders retain the study hierarchy.

`ok`, `needs_review` and `failed` describe operational results. They do not
measure segmentation accuracy. See [clip names and report fields](docs/OUTPUTS.md).

## Repository map

| Path | Purpose |
| --- | --- |
| `video_processor.py` | Shared reader, matcher and FFmpeg exporter |
| `instagram_processor.py` | Instagram icon and layout checks |
| `tiktok_processor.py` | TikTok icon checks |
| `IG_*_template.png`, `TK_*_template.png` | Six interface templates |
| `run_hungary_splits.py` | Linux batch launcher |
| `main*.py` | Legacy local and Slurm entry points |
| `Run_in_Roihu.ipynb` | Notebook launcher |
| `archive/` | Recorded experiments and reference material |

## Documentation

[Environment](docs/ENVIRONMENT.md) · [Instagram rules](docs/INSTAGRAM.md) · [TikTok rules](docs/TIKTOK.md) · [Exact method](docs/METHOD.md) · [Legacy Slurm workflow](docs/SLURM.md) · [Running instructions](docs/RUNNING.md) · [Outputs](docs/OUTPUTS.md) · [Recorded evidence](docs/EVIDENCE.md)
