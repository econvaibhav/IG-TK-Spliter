# Spliter

**Split an Instagram or TikTok MP4 screen recording into candidate feed-item clips.**

OpenCV detects interface cues; FFmpeg exports the resulting intervals.
The original recording is kept. Run it with ordinary Python on your computer.

![Spliter workflow: frame preparation, detector evidence, boundary rules and clip export](workflow.png)

The command selects the platform explicitly and reads duration from MP4 metadata.
The image summarizes the detector and export sequence.

## Install

Use Python 3.10+ and FFmpeg 5.1+ with `ffmpeg` and `ffprobe` on your PATH.
FFmpeg must include the `libx264` encoder. Install FFmpeg through your system's
package manager or the [FFmpeg download page](https://ffmpeg.org/download.html).

```bash
git clone https://github.com/econvaibhav/IG-TK-Spliter.git
cd IG-TK-Spliter
python3 -m venv .venv
```

Activate the environment with `source .venv/bin/activate` on macOS/Linux, or
`.venv\Scripts\Activate.ps1` in Windows PowerShell, then run:

```bash
python -m pip install -r requirements.txt
ffmpeg -version
ffprobe -version
ffmpeg -hide_banner -h encoder=libx264
```

The last command should describe `Encoder libx264`. A successful version check
alone does not mean FFmpeg includes the encoder needed to export clips.
On Windows, use `python` instead of `python3` when creating the environment.

### Fedora: enable H.264 export

If exporting fails with `Unknown encoder 'libx264'`, install the full FFmpeg
build from RPM Fusion. These steps enable its free repository and replace
`ffmpeg-free`. Run each command separately and review DNF's proposed package
changes before confirming:

```bash
sudo dnf install "https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm"
sudo dnf swap ffmpeg-free ffmpeg --allowerasing
```

Then check that the encoder is listed:

```bash
ffmpeg -hide_banner -encoders 2>/dev/null | grep libx264
```

Continue once a line containing `libx264` appears. If DNF reports a dependency
error, resolve that installation error before rerunning the splitter. This is a
system FFmpeg installation; it does not require recreating the Python environment.
See [RPM Fusion setup](https://rpmfusion.org/Configuration) and its
[multimedia guide](https://rpmfusion.org/Howto/Multimedia).

## Split one recording

Choose the platform explicitly. The input can be anywhere; it does not need a
particular folder structure. Quote paths containing spaces.

```bash
python main.py "/path/to/recording.mp4" --platform instagram
python main.py "/path/to/recording.mp4" --platform tiktok --output "/path/to/new_clips"
```

The default output is a new `recording_splits` folder beside the input.
With `--output split_run`, clips go into `split_run` under your terminal's current
directory. Use an absolute output path to choose the location explicitly. For
example, on Linux or macOS:

```bash
python main.py "$HOME/Downloads/video_TK.mp4" \
  --platform tiktok \
  --output "$HOME/Downloads/video_TK_clips"
```

An existing output folder is refused: choose a different `--output` for another
run. A failed export can leave a folder containing its report or completed clips.
After fixing the error, select a new output folder; no deletion is required.
The original MP4 is preserved.

| Option | Meaning |
| --- | --- |
| `--platform instagram\|tiktok` | Required detector selection |
| `--output PATH` | New folder for clips and reports |
| `--instagram-mode both\|reels\|feed` | Both Instagram checks by default; restrict them when the recording contains only one interface |
| `--threshold 0.85` | Normalized icon-match threshold; increasing it accepts fewer matches |
| `--templates-dir PATH` | Folder containing the selected platform’s replacement PNGs, using the existing filenames |
| `--detect-only` | Write boundaries and a report without encoding clips |

For example, inspect candidate boundaries in a Reels-only recording:

```bash
python main.py recording.mp4 --platform instagram --instagram-mode reels --detect-only --output preview
```

Use a separate directory for the real export after a preview:

```bash
python main.py recording.mp4 --platform instagram --instagram-mode reels --output clips
```

Open several exported clips and check the start/end times in `segments.csv`.
A successful run alone does not establish that each interval is one post.
For several files, run the command once per recording with a distinct output
folder. Choose the platform for each recording explicitly.

The same command is available as `python -m spliter` from the repository root.
You can also call `/absolute/path/IG-TK-Spliter/main.py` from another directory;
bundled templates are resolved relative to the source files.

## Matching images

The original six templates are kept in separate platform folders:

| Platform | Folder | Images |
| --- | --- | --- |
| Instagram | `templates/instagram/` | [Heart](templates/instagram/IG_heart_template.png), [comment](templates/instagram/IG_comment_template.png), [share](templates/instagram/IG_share_template.png) |
| TikTok | `templates/tiktok/` | [Heart](templates/tiktok/TK_heart_template.png), [share](templates/tiktok/TK_share_template.png), [save](templates/tiktok/TK_save_template.png) |

These are the actual matching images, not illustrations. Their bytes are unchanged.
The default folder is selected automatically by `--platform`. For replacement
Instagram templates, for example, use `--templates-dir /path/to/my_instagram_icons`.

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
with a warning. Candidate cuts leaving less than one nominal frame at the end
are skipped, keeping that tail in the final clip. Each export must contain a
video stream with readable packets before it is marked successful. Decoding
that ends well before the reported video end fails instead of silently reporting
a complete run.

## When to check or adjust the result

This is an interface-position heuristic for screen-recorded feeds. It does not
identify posts, recover downloaded originals, or find scene changes in arbitrary
videos. Cuts are candidates for review.

| Situation | What to do |
| --- | --- |
| App layout, icon size or recording crop differs | Review clips and supply matching templates; the fixed position rules may also need adjustment |
| Too many cuts | Check the visible interface and selected Instagram mode; a stationary icon inside a trigger zone can repeatedly satisfy the rule |
| Few or no cuts | Check platform, full-screen layout and templates; lowering the threshold also increases false matches |
| Missing template or recording too narrow | Restore the template files or use a recording that includes the expected interface |
| Missing audio | Supported automatically; video-only clips are written |
| Invalid metadata, unreadable frames or a truncated file | Repair/remux the recording and run again into a new output folder |
| Timestamp warning on variable-frame-rate video | Inspect the boundaries; FPS fallback is approximate |
| `Unknown encoder 'libx264'` | Install an FFmpeg build containing `libx264`; on Fedora, follow [the steps above](#fedora-enable-h264-export) |
| `Output already exists` after a failed attempt | Choose a new `--output`; the previous folder can remain in place |
| FFmpeg error | Read the reported message and check FFmpeg, `libx264`, disk space and output permissions |

Review representative recordings from each device and interface layout before
processing a large collection. Re-encoding and heuristic timestamps mean cuts
are not guaranteed to be lossless or exact to a particular source frame.

## Verification

Synthetic MP4 checks passed for Instagram and TikTok icon transitions, audio and
silent inputs, odd dimensions, variable frame rates, paths with spaces, preview
mode, existing-output protection and cuts near the final frame. Exported clips
were checked with ffprobe and decoded with FFmpeg; input file hashes were unchanged.
These checks verify the matching and export mechanics, not boundary accuracy on
real recordings. Review clips from your own device before a large run.

## Files

| File | Purpose |
| --- | --- |
| `main.py` | Small launcher, preserving the existing command |
| `spliter/cli.py` | Command-line arguments and detector selection |
| `spliter/video_processor.py` | Validation, frame reading, matching, export and reports |
| `spliter/instagram_processor.py` | Instagram icon and feed-layout rules |
| `spliter/tiktok_processor.py` | TikTok icon rules |
| `templates/instagram/` | Three Instagram matching templates |
| `templates/tiktok/` | Three TikTok matching templates |
| `workflow.png` | Workflow image displayed above |
| `requirements.txt` | OpenCV and NumPy dependencies |

Author: **Vaibhav Agarwal**.
