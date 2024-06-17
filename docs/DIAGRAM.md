# Workflow diagram

The figure explains the actual processing sequence for readers of the repository
and research documentation. A setup row leads to a detector-and-rule table,
then the two outcomes: keep scanning, or export a segment and advance its start.
The only color accent, green, identifies an accepted cut and its export.

## Read the workflow

1. **Open the recording.** The folder path identifies Instagram or TikTok.
   The shared processor obtains FPS and frame count, estimates duration as
   frame count divided by FPS, and sets the first segment start to zero.
2. **Read and prepare a frame.** OpenCV decodes one frame at a time. Analysis
   uses a 960-pixel-high image with the original aspect ratio. Each detector
   applies its own bright-pixel mask, grayscale conversion and closing.
   Instagram also uses contour filling and, for its layout rule, extra shape
   processing. The shared preparation box summarizes these detector-specific
   operations; a single cleaned image is not reused for all detectors.
3. **Find a cue and test the rule.** The table pairs each detector's evidence
   with the conditions that accept a cut. Both a position/geometry condition
   and a minimum elapsed-time condition must pass. Template correlation of
   at least 0.85 is a match score, not an accuracy measurement. The returned
   icon coordinate is the first qualifying top-left location with `x > 360`
   pixels in the resized image.
4. **Act on an accepted cut.** FFmpeg exports the original screen recording
   from the current segment start to the accepted timestamp, including video
   and audio. The part counter advances and that timestamp becomes the new
   segment start. Finish the remaining checks for this frame before reading
   the next one. With no accepted cut, keep the segment start unchanged.
5. **Finish reading.** At the first failed frame read, the base processor exports
   the remaining interval to its estimated duration. This can be a decoder
   stopping early as well as normal completion.

## Instagram's two checks

Instagram always runs the icon check first and the layout check second on each
frame. It does not first classify the content as a Reel or a feed video. Both
checks share the segment start and part counter. An icon cut immediately
updates that shared start, so the layout rule sees the reset time gap on the
same frame. The diagram's accepted-cut outcome applies immediately whenever
a detector passes its rule; it does not postpone export until both checks finish.

TikTok uses only its heart/share/save icon detector, with different vertical
thresholds for the three icons. Any passing icon can trigger a cut once the
elapsed-time condition is also satisfied.

## Details kept in the method reference

The figure includes the normalization height, matching threshold, horizontal
match restriction and minimum time gaps. The full bright-pixel ranges, per-icon
vertical thresholds, contour dimensions and timestamp adjustment are listed
in [METHOD.md](METHOD.md). Candidate time is the current frame timestamp plus
`1.5/fps`.

These are deterministic interface rules. The algorithm tests the current
frame's positions rather than tracking motion or identifying semantic content.
Exports retain the screen-recorded interface and are candidate feed-item clips
for review. The cleaned analysis image is not the exported video. See
[RUNNING.md](RUNNING.md) for launcher and input handling.

## Build from LaTeX

The source is self-contained TikZ. Install LaTeX with TikZ, standalone and Latin
Modern, plus Poppler, then run from the repository root:

```bash
bash tools/build_diagram.sh
```

This creates `docs/figures/feedslicer_workflow.pdf`, `.png` and `.svg` from
`feedslicer_workflow.tex`. The README displays the PNG; PDF and SVG retain
vector artwork. Video-processing dependencies are not needed to build it.
