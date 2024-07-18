# Scope and limitations

FeedSlicer detects candidate feed transitions from interface geometry. Its
rules depend on app layout, template scale, icon appearance and recording
dimensions. It does not identify post IDs, creators or semantic boundaries.

| Area | Practical implication |
| --- | --- |
| Fixed template sizes | Different interface scaling can reduce matching quality |
| Bright-pixel masks | Bright content can imitate interface shapes; colored icons may disappear |
| Position tests | No tracking across frames confirms that a transition occurred |
| Time gaps | Reduce closely spaced cuts but do not ensure one post per clip |
| Failed frame reads | The base processor treats them as the end, even if decoding stopped early |
| Estimated duration | Frame-count/FPS duration can disagree with presentation timestamps |
| Existing output paths | The base exporter skips them without validating their contents |
| Encoding | FFmpeg defaults do not promise lossless or frame-exact cuts |

Use the batch launcher to preserve source recordings, then inspect clips and
logs before downstream analysis. The launcher checks operational completion;
it does not provide ground-truth accuracy or complete temporal-coverage checks.

## Evaluation that would be useful

Compare candidate cuts against manually annotated feed changes across devices
and app versions. Report matching tolerance, false positives, missed changes,
and clip coverage. No such boundary-level evaluation is included here.
