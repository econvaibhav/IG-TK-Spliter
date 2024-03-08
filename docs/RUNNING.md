# Run FeedSlicer

## Input folders

The Linux batch launcher `run_hungary_splits.py` accepts this study structure:

```text
Hungary_Organised/Fidesz/1/20240328/Instagram/recording.mp4
Hungary_Organised/Fidesz/1/20240328/TikTok/recording.mp4
```

| Level | Accepted value |
| --- | --- |
| Party | `Fidesz` or `Tisza` |
| Participant | `1`, `2`, `3` or `4` |
| Date | A valid calendar date in `YYYYMMDD` form |
| Platform | Instagram or TikTok, case-insensitive |
| File | A regular MP4 file; input symlinks are rejected |

These paths illustrate the folder format. Set `--input` to the dataset root;
`--scope Fidesz/1` selects the relative subtree. Input and output roots must be
separate and non-overlapping. Avoid `.mp4` within output directory names.

## Preserve the source recordings

The base processor deletes its input pathname after its final export. The
launcher supplies a private symbolic link named `input.mp4`, so this removes
the staging link. It redirects exports into a fresh run directory and closes
both OpenCV and MoviePy resources.

After each job it compares source device, inode, size and modification time.
This metadata check does not hash the recording contents.
