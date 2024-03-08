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

## Environment

Use a separate Python environment and an FFmpeg executable.
See [environment setup](docs/ENVIRONMENT.md) for the compatibility versions.

## Repository map

| Path | Purpose |
| --- | --- |
| `video_processor.py` | Shared reader, matcher and FFmpeg exporter |
| `instagram_processor.py` | Instagram icon and layout checks |
| `tiktok_processor.py` | TikTok icon checks |
| `IG_*_template.png`, `TK_*_template.png` | Six interface templates |
| `run_hungary_splits.py` | Linux batch launcher |
| `main*.py` | Legacy local and Slurm entry points |

## Documentation

[Environment](docs/ENVIRONMENT.md) · [Instagram rules](docs/INSTAGRAM.md) · [TikTok rules](docs/TIKTOK.md) · [Exact method](docs/METHOD.md) · [Legacy Slurm workflow](docs/SLURM.md) · [Running instructions](docs/RUNNING.md)
