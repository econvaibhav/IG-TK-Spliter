# Code walkthrough

## Files and responsibilities


| File | Detailed role |
| --- | --- |
| `video_processor.py` | Opens MoviePy/OpenCV readers; stores FPS, count, duration, geometry and segment state; performs normalized template matching; calls FFmpeg; loops over resized frames; exports the tail and deletes the input name. |
| `instagram_processor.py` | Inherits shared state; runs icon-position rules and a separate feed-layout rule on each frame; both detectors use the same segment counter/start time. |
| `tiktok_processor.py` | Inherits shared state; applies three icon-position rules and the 0.4-second minimum gap. |
| `main.py` | Loads templates from the current working directory; dispatches a fixed list of seven Finland recordings by their parent folder name. The function parameter is not used for discovery. |
| `main_array_generate.py` | Contains duplicate wrapper/array functions; its active top-level call generates `Spain.txt` by walking a fixed Spain directory. |
| `main_array.py` | Reads `Spain.txt`; maps `SLURM_ARRAY_TASK_ID - 1` to one entry; dispatches by `Instagram`/`Tiktok`. |
| `run_hungary_splits.py` | Linux batch runner with CLI, study-schema validation, process workers, temporary input links, output redirection, logging and run reports. |
| `Run_in_Roihu.ipynb` | Original notebook around that runner, including preflight and process-group termination on interrupt. |
| `archive/notebooks/test.ipynb` | Original exploration, recovery/copy commands, dependency troubleshooting, isolated environment setup and recorded 48-video run. |
| `archive/notebooks/ffmpeg_diagnostics.ipynb` | Reads saved failure logs and compares original export settings with an added video-track-timescale option for one recording. |

Read [METHOD.md](METHOD.md) for the numerical thresholds and [RUNNING.md](RUNNING.md) for operation.

## Shared processor: exact control flow

1. Construction opens `VideoFileClip(video_url)` and `cv2.VideoCapture(video_url)`. It obtains `fps`, total frames and geometry without first checking for a valid, positive FPS or dimensions.
2. Duration is estimated as frame count divided by FPS. Width for analysis is computed from the aspect ratio with a fixed 960-pixel height.
3. The output directory is the input pathname split at the first literal `.mp4`. This is not a general suffix-removal function; it is case-sensitive and also matches directory components.
4. Each successful read is resized and dispatched to the platform's `process_frame`. Returned images are unpacked but neither displayed nor saved. The frame counter increments after detector/export work completes.
5. A failed read is treated as the end of the recording. It is not distinguished from a decoder failure. The final interval uses the estimated duration, then `os.remove(self.video_url)` executes.
6. OpenCV is released after the loop, but the base implementation has no `try/finally` resource cleanup and does not explicitly close its MoviePy reader.

The final segment can be tiny or invalid if the last candidate boundary exceeds duration. Variable-frame-rate recordings may expose differences between frame-count-based duration and presentation timestamps. These are potential issues inferred from the calculations, not measured failure rates.

## Template matching details that matter

The minimum match score passed by both platform classes is 0.85. The method's own default of 0.90 is not used by those calls. Accepted locations are found by `np.where`; the first one with top-left `x > 360` supplies the returned `y`.

This means:

- It does not choose the highest score or group overlapping detections.
- It does not compare motion across frames.
- The hard-coded horizontal cutoff is applied after resizing and is not a relative fraction of frame width.
- Match rectangles are drawn into the same grayscale image subsequently used for the second and third templates.
- White content can resemble or obscure interface shapes, and colored/filled interface states may not pass the bright mask.

The current PNG dimensions and the numerical region tests are recorded in the method document. All six template files decoded successfully during static review.

## Export behavior and failure handling

`split_video` skips an output path if it already exists, including an empty or partial output from an interrupted attempt. It calls `ffmpeg.input(..., ss=start_time, to=end_time)` and requests AAC audio with `strict='experimental'` and 192 kb/s. There is no explicit video codec, stream-copy mode, timestamp repair or overwrite option.

FFmpeg errors propagate. The commented-out audio fallback is inactive. Exporting a segment is synchronous inside the frame loop, so scanning pauses while FFmpeg exports. The code is therefore not a single-pass decoder/exporter and makes no verified real-time throughput guarantee.

Successful completion directly deletes the passed input name. Directly calling the original processors or their legacy wrappers with an original recording is therefore destructive. The supplied Hungary runner avoids this by passing a private symlink.

## Batch runner

| Stage | Behavior |
| --- | --- |
| Dependency setup | Requires an FFmpeg executable, directs MoviePy to it, imports the expected `ffmpeg-python` API, loads every template, and sets OpenCV to one thread. |
| Discovery | Scans only the selected subtree, sorts directory/file names, accepts MP4 extensions case-insensitively, rejects input symlinks, and validates exactly five relative path components. |
| Scope | Supports Fidesz/Tisza, participants 1-4, valid calendar dates, and Instagram/TikTok. Defaults to Fidesz/1. |
| Resources | Uses spawned process workers, one assigned CPU per worker, and thread-pool environment settings. FFmpeg inherits process affinity; this limits scheduling, not the count of threads every library may create. |
| Job setup | Makes a private staging directory and input link; overrides only the processor instance's output directory. Detection and encoding code remain unchanged. |
| Result checks | Requires non-empty MP4 exports; compares processed and expected frame counts; checks original file metadata after processing. |
| Reporting | Writes one row per completed job, per-video logs, run configuration, selected paths and processor hashes. |
| Reruns | Creates a new run directory with a timestamp and random suffix, avoiding stale outputs that the base exporter would skip. |

The source metadata check compares device, inode, size and nanosecond modification time. It cannot prove byte identity by itself. The runner does not validate clip duration, decodability, temporal coverage, uniqueness or one-post-per-clip accuracy. It does not hash the raw recordings.

A job can produce some partial outputs and still report zero clips/frames on failure because counters are copied into the report only after the processing method returns. This distinction matters when interpreting a failed run.

## Legacy entry points

The three `main*` scripts have top-level calls and no `if __name__ == '__main__'` guard. Importing them starts their configured work. Their behavior is preserved for auditability.

The file-list generator accepts any file in appropriately named directories, not only MP4s. It skips paths whose immediate grandparent is exactly `Others`, uses `os.walk` order, and writes a JSON list into a `.txt` file. The legacy array runner assumes the manifest exists and the Slurm variable is a valid integer. It checks only `task_id < len(all_files)`; nonpositive Slurm values can produce negative Python indices.

These scripts use exact `Tiktok` casing. The supplied modern batch runner normalizes platform names to lowercase and handles `TikTok` as expected. The two dispatch systems should not be described as identical.

## Evidence from the notebooks

The original `test.ipynb` contains a saved preflight reporting 48 inputs and a run summary reporting 40 `ok`, 1 `needs_review`, and 7 `failed`. The run directory is dated 20 September 2026. The notebook also records a MoviePy 2.x import failure and a dependency conflict after a downgrade in the Jupyter environment. Later cells set up a separate MoviePy 1.x runtime.

The diagnostic notebook shows `pts/dts pair unsupported` during an MP4 export. On one 30-second export attempt, adding `-video_track_timescale 90000` changed a failure into a success. This is evidence for one diagnostic attempt only. It is not proof that all seven failed recordings have the same cause or that the setting is a universal repair. The source exporter has not been changed to add it.

The standalone `part_1 (2).mp4` failed the local FFprobe check with `moov atom not found`. It was left untouched and excluded from the repository. Its filename alone cannot establish which run produced it.

The older archived README describes tests performed during an earlier task. Those statements remain inside the unchanged original document; this review does not claim to have repeated them. Source hashes and static checks are described in the verification guide when available.

## Potential future work, not implemented

Make deletion opt-in; expose thresholds and platform geometry as configuration; validate frames, FPS, input templates and exports; record a structured boundary table; separate pure detection from export; stabilize file discovery; add a tested general launcher; evaluate boundaries against human annotations across devices and app versions. These are review findings and research opportunities, not features of this unchanged snapshot.
