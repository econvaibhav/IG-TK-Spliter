# Method: interface cues to clip boundaries

## 1. Decode and normalize the analysis image
`VideoProcessor` opens the recording with both MoviePy and OpenCV. OpenCV provides FPS, frame count and dimensions. The estimated duration is `total_frames / fps`. Each decoded frame is resized to height $H=960$ and width $W=\lfloor960w/h\rfloor$, keeping its aspect ratio.

Only the analysis image is resized. Exports read the original input video through FFmpeg; they are not videos of the processed grayscale frames.

## 5. Export and continue
An accepted boundary exports the interval from $s$ to $t$ from the original recording, increments the shared counter, and sets $s=t$. Processing then continues with later frames. At the first failed `cap.read()`, the base class exports a final interval to `total_frames / fps` and removes its input pathname.

The FFmpeg wrapper uses input-side `ss` and `to`, asks for AAC audio at 192 kb/s, and leaves the video codec to FFmpeg defaults. It does not specify stream copy. Do not describe the output as lossless or promise frame-exact cuts. Existing output paths are skipped without checking completeness.
