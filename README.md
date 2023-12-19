# FeedSlicer

**Split Instagram and TikTok screen recordings into candidate post-level clips.**

FeedSlicer uses on-screen interface cues to find possible transitions between
feed items. OpenCV checks icon positions and feed geometry; FFmpeg exports
the intervals from the recording.

## How it works

| Step | Behavior |
| --- | --- |
| Frame processing | Reads frames individually and resizes the analysis image to 960 pixels high. |
| Export | Writes numbered MP4 clips from the original recording, with AAC audio. |

## Environment

Use a separate Python environment and an FFmpeg executable.
See [environment setup](docs/ENVIRONMENT.md) for the compatibility versions.

## Documentation

[Environment](docs/ENVIRONMENT.md) · [Instagram rules](docs/INSTAGRAM.md)
