# Fidesz/1 test: 32-worker launcher

The only new processing file is `run_hungary_splits.py`. The three processor files
and six PNG templates are byte-for-byte copies of your attachments, with their
normal import filenames restored. `unchanged_files.json` records their SHA-256
checksums. No detection thresholds, frame processing, boundary calculations or
FFmpeg encoding arguments have been edited.

## What to change

Use `run_hungary_splits.py` instead of launching `main.py`, `main_array.py` or
`main_array_generate.py`. Those older entry points select Finland/Spain paths,
use the spelling `Tiktok`, and the array entry point expects a Slurm array job.
The new launcher scans only `Hungary_Organised/Fidesz/1`, includes all dates and
both Instagram and TikTok beneath it, and starts
32 independent video-worker processes inside your existing interactive session.

No edits to `video_processor.py`, `instagram_processor.py` or
`tiktok_processor.py` are needed.

| Setting | Configured value |
| --- | --- |
| Dataset root | `/scratch/project_2009497/Hungary_Data_Test/Hungary_Organised` |
| Only process | `/scratch/project_2009497/Hungary_Data_Test/Hungary_Organised/Fidesz/1` |
| Output parent | `/scratch/project_2009497/Hungary_Data_Test/Hungary_Splits_Fidesz1_Test` |
| Workers | `32` |
| Discovery | `.mp4` only, recursively; original Party/Participant/Date/Platform folders retained |

`--input` is the dataset root used to preserve the output hierarchy. `--scope`
selects the subtree to scan and defaults to `Fidesz/1`. Do not replace the dataset
root with the participant directory; the scope already selects that directory.

## Why originals survive

Your uploaded `video_processor.py` actively calls `os.remove(self.video_url)`
after processing. Passing an original video pathname directly would delete it.

This launcher creates a private symbolic link for each job and passes that link
to the unchanged processor. Reads follow the link to the video; deletion removes
only the link. The launcher sets the instance's `output_dir` to its own separate
split folder before calling the original `process_video()` method. Originals are
never renamed, moved, overwritten, passed to a deletion call, or fully duplicated
for processing. Their contents must remain available throughout the run.

## Run in your Roihu Jupyter session

Upload `hungary_fidesz1_test_32workers.zip` beside your notebook. In a new cell:

```python
from pathlib import Path
from zipfile import ZipFile
import sys

with ZipFile("hungary_fidesz1_test_32workers.zip") as archive:
    archive.extractall("Fidesz1_Split_Test")

runner = Path("Fidesz1_Split_Test/hungary_fidesz1_test_32/run_hungary_splits.py").resolve()
print(runner)
```

Check that input, imports, image templates and CPU access are ready. The output
should say `ONLY PROCESSING: /scratch/project_2009497/Hungary_Data_Test/Hungary_Organised/Fidesz/1`:

```python
!{sys.executable} -u "{runner}" --workers 32 --scope Fidesz/1 --check-only
```

Then start splitting:

```python
!{sys.executable} -u "{runner}" --workers 32 --scope Fidesz/1
```

The launcher uses your notebook's Python executable, and thus the same selected
python-data environment. It prints a completion line per video and a status line
every 30 seconds while waiting. Detailed per-video progress and exceptions are
written to the run's `_logs` directory.

The archive also contains `Run_in_Roihu.ipynb`, which you can open after extracting
and run from its folder. That notebook's launch helper stops its own worker and
FFmpeg process group when you interrupt the launch cell.

## Dependencies

The preflight checks the actual imports instead of assuming they are installed.
The supplied processors use `moviepy.editor`, which is absent from MoviePy 2.x.
Keeping the code unchanged therefore requires MoviePy 1.x. If preflight reports
missing MoviePy or `moviepy.editor`, install in your Jupyter environment:

```python
%pip install "moviepy==1.0.3" ffmpeg-python
```

If OpenCV is also missing, install it separately:

```python
%pip install "opencv-python-headless<4.12"
```

NumPy is also required. A real `ffmpeg` executable must be available in the
session's PATH; `ffmpeg-python` is only its Python interface. The launcher uses
that executable for both FFmpeg and MoviePy. If it is missing, make the executable
available in the session before running preflight again.

MoviePy documents its 2.x import changes here:
https://zulko.github.io/moviepy/getting_started/updating_to_v2.html

## Where the splits go

Each invocation creates a fresh directory and prints its exact name. For example:

```text
/scratch/project_2009497/Hungary_Data_Test/Hungary_Splits_Fidesz1_Test/run_20260918_170000_ab1234/Fidesz/1/20260322/Instagram/az_recorder_20260322_154413/part_1_reel.mp4
```

The hierarchy is `run/Party/Participant/Date/Platform/OriginalVideoStem/clip.mp4`.
The extra video folder prevents two recordings on the same date from overwriting
each other's `part_1.mp4` and subsequent clips.

| Run item | Meaning |
| --- | --- |
| `summary.csv` | Original pathname, split folder, status, number of clips, frame counts, note and log pathname |
| `_logs/00001.log` etc. | Output from the original splitting code and any exception/FFmpeg error |
| `run_config.json` | Selected scan scope, full input-to-output mapping, worker count and processor checksums |
| `_work` | Private temporary input links; normally removed after their jobs complete |

A rerun creates another fresh run directory. It does not resume into an older
partial clip folder or overwrite earlier splits. This matters because the
unchanged processor skips any clip filename that already exists, even if that
file came from an interrupted run. An interrupted run can retain partial clips
or staging links; the originals remain in their input folder.

## Resources and verification limits

The launcher uses 32 process workers, assigns each one a distinct available CPU,
sets OpenCV to one thread, and limits common BLAS/OpenMP thread pools. FFmpeg child
processes inherit their worker's CPU affinity. This limits CPU scheduling; it does
not promise that every native library creates only one thread. Memory use still
depends on recording resolution and codec, so 32 GB is an allocation rather than
a guarantee that all possible inputs fit simultaneously.

`ok` means the unchanged processor returned, produced non-empty clips, and did not
stop short of its reported frame count. This is not a full scientific validation
of detected boundaries or every output frame. A single clip is explicitly noted
as having no detected split boundaries. Failures and short reads are reported.

## Tests performed

The original processors and launcher were run on two short synthetic videos with
the supplied icon templates, one Instagram and one TikTok. Both detected a
transition and produced two FFprobe-readable clips. Both original SHA-256 hashes
remained unchanged. A second launcher run created a separate directory and left
the first run intact. These end-to-end tests used two parallel workers because
the test workspace has fewer than 32 CPUs; the delivered default is 32 for your
Roihu session. A further scoped test included Fidesz/1 Instagram and TikTok inputs alongside
Fidesz/3 and Tisza/2 exclusion fixtures. Only Fidesz/1 was selected and processed;
all originals stayed unchanged. The full Hungary recordings have not been processed here.
