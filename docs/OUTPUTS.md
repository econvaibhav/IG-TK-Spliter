# Output clips and run reports

Each invocation writes a new directory and retains the input study hierarchy:

```text
run_<timestamp>_<suffix>/Fidesz/1/20240328/Instagram/recording/part_1_reel.mp4
```

| Clip name | Boundary source |
| --- | --- |
| `part_N_reel.mp4` | Instagram icon rule |
| `part_N_video.mp4` | Instagram feed-layout rule |
| `part_N.mp4` | TikTok rule, or the final trailing segment on either platform |

Numbering follows a shared counter within each recording. FFmpeg exports from
the original recording, including the recorded interface. The resized and
masked analysis frames are not the exported video.

Audio is requested as AAC at 192 kb/s. The video codec is left to FFmpeg's
defaults; the code does not request stream copy or guarantee lossless,
frame-exact cuts.
