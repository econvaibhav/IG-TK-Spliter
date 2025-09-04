# FeedSlicer

**Split an Instagram or TikTok MP4 screen recording into candidate feed-item clips.**

OpenCV detects interface cues; FFmpeg exports the resulting intervals.
The original recording is kept. Run it with ordinary Python on your computer.

![FeedSlicer workflow: frame preparation, detector evidence, boundary rules and clip export](workflow.png)

The command selects the platform explicitly and reads duration from MP4 metadata.
The image summarizes the detector and export sequence.

## Install

Use Python 3.10+ and FFmpeg 5.1+ with `ffmpeg` and `ffprobe` on your PATH.
FFmpeg must include the `libx264` encoder. Install FFmpeg through your system's
package manager or the [FFmpeg download page](https://ffmpeg.org/download.html).

```bash
git clone https://github.com/econvaibhav/IG-TK-Spliter.git
cd IG-TK-Spliter
python -m venv .venv
```

Activate the environment with `source .venv/bin/activate` on macOS/Linux, or
`.venv\Scripts\Activate.ps1` in Windows PowerShell, then run:

```bash
python -m pip install -r requirements.txt
ffmpeg -version
ffprobe -version
```

## Split one recording

Choose the platform explicitly. The input can be anywhere; it does not need a
particular folder structure. Quote paths containing spaces.

```bash
python main.py "/path/to/recording.mp4" --platform instagram
python main.py "/path/to/recording.mp4" --platform tiktok --output "/path/to/new_clips"
```

The default output is a new `recording_splits` folder beside the input.
An existing output folder is refused: choose a different `--output` for another run.

| Option | Meaning |
| --- | --- |
| `--platform instagram\|tiktok` | Required detector selection |
| `--output PATH` | New folder for clips and reports |
| `--instagram-mode both\|reels\|feed` | Both Instagram checks by default; restrict them when the recording contains only one interface |
| `--threshold 0.85` | Normalized icon-match threshold; increasing it accepts fewer matches |
| `--templates-dir PATH` | Replacement PNG templates, using the six existing filenames |
| `--detect-only` | Write boundaries and a report without encoding clips |

For example, inspect candidate boundaries in a Reels-only recording:

```bash
python main.py recording.mp4 --platform instagram --instagram-mode reels --detect-only --output preview
```

For several files, run the same command once per recording with a distinct output
folder. Keep platforms separate when choosing the detector.

## What you get

- `part_0001.mp4`, `part_0002.mp4`, ...: consecutive candidate intervals.
- `segments.csv`: filename, start, end, duration, boundary reason and whether
  the interval was exported.
- `report.json`: input, settings, decoded frame count, warnings and run status.

With `--detect-only`, MP4s are not created; CSV filenames describe planned clips.
No detected boundaries means one whole-recording interval, marked for review.
Clips use H.264 video and AAC audio when the recording has audio. Silent recordings
are supported. Exports retain the source's displayed resolution, with up to one
padding pixel on an odd-width or odd-height edge for H.264 compatibility.
The 960-pixel analysis image is never used as the exported video.

`completed` means the run finished. `needs_review` means it finished with warnings,
such as no detected transition or approximate timing. Neither is an accuracy score.
A failed run exits with an error; any completed clips and its report remain in that
run's folder as partial results.

## Detection method

1. **Read and prepare frames.** Decode each frame and resize it to height
   `H = 960`, preserving aspect ratio.
2. **Isolate bright shapes.** Mask each BGR channel, convert to grayscale, and
   close gaps using a 2-by-2 elliptical kernel.
3. **Find interface evidence.** Match icon templates and, for Instagram feed
   views, inspect wide four-corner shapes.
4. **Accept a boundary.** Apply the detector's position rule and minimum elapsed
   time since the previous accepted cut.
5. **Export and continue.** Export from the previous cut to this boundary, then
   continue reading. Export the remaining tail at the end.

| Detector | Frame cleanup | Position rule at height 960 | Minimum gap |
| --- | --- | --- | --- |
| Instagram icons | BGR 230–255; fill contours with area >50 | Heart, comment or share: `90 < y < 860` and either `y < 320` or `y > 807.62` | Strictly >0.4 s |
| Instagram feed | BGR 250–255; contour fill, dilation, erosion, side borders and inversion | Four-corner contour: width >image width−20; `45 ≤ y ≤ 120`; `150 ≤ height ≤ 200` | Strictly >1 s |
| TikTok icons | BGR 220–255; no contour fill | Heart `y ≤ 480`, share `y ≤ 600`, or save `y ≤ 564.71`; each also accepts `y > 807.62` | Strictly >0.4 s |

Icon matching uses `TM_CCOEFF_NORMED` and accepts scores at least the selected
threshold, normally 0.85. It takes the first qualifying location in row order
with top-left `x > 360`; `y` is the icon's top-left coordinate. Each template
sees the same unmodified prepared image. Templates are fixed-size grayscale PNGs.

Instagram evaluates icons before feed geometry on each frame. Both share the
last accepted boundary, so an icon cut prevents a second cut on the same frame.

The candidate cut time uses the decoded frame timestamp plus the original
`1.5 / FPS` adjustment, bounded by the video end. Duration comes from the video
stream metadata. Missing or repeated OpenCV timestamps use approximate FPS timing
with a warning. Decoding that ends well before the reported video end fails
instead of silently reporting a complete run.

