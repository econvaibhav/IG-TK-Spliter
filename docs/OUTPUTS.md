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

## Run reports

| File | Contents |
| --- | --- |
| `summary.csv` | `source`, `output`, `status`, `clips`, `frames`, `expected_frames`, `note`, `log` |
| `_logs/*.log` | Per-video processor output, exceptions and captured FFmpeg errors |
| `run_config.json` | Selected scope, worker count, path mapping and processor hashes |

## Job status

| Status | Meaning |
| --- | --- |
| `ok` | Processing returned, exports are non-empty, and reading did not stop short of the reported frame count |
| `needs_review` | Reading stopped early, or source metadata changed after an otherwise successful job |
| `failed` | A processor, export, input-access or worker failure was observed |

`ok` is an operational check, not a boundary-accuracy score. One non-empty clip
can mean no transitions were detected. These checks do not validate temporal
coverage, clip decodability or whether every clip contains exactly one post.
