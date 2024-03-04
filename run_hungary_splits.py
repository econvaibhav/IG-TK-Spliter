"""Test the supplied, UNCHANGED splitters on Fidesz/1 using 32 workers.

Only this launcher is new. The processor files and image templates are unchanged.
The old processor deletes its input name. Each worker therefore passes a private
symbolic link, never an original pathname; deleting that link preserves the video.
Every invocation gets a fresh output directory so existing clips are not reused.
"""

import os

# Set BEFORE importing NumPy/OpenCV/MoviePy, including in spawned workers.
for _key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
             "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "BLIS_NUM_THREADS"):
    os.environ[_key] = "1"

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from contextlib import redirect_stdout, redirect_stderr
import csv
from datetime import datetime
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
import shutil
import sys
import traceback
import uuid


INPUT_ROOT = Path("/scratch/project_2009497/Hungary_Data_Test/Hungary_Organised")
INPUT_SCOPE = Path("Fidesz/1")
OUTPUT_ROOT = Path("/scratch/project_2009497/Hungary_Data_Test/Hungary_Splits_Fidesz1_Test")
WORKERS = 32
HERE = Path(__file__).resolve().parent
TEMPLATE_NAMES = {
    "instagram": ("IG_heart_template.png", "IG_comment_template.png", "IG_share_template.png"),
    "tiktok": ("TK_heart_template.png", "TK_share_template.png", "TK_save_template.png"),
}
PROCESSORS = None
TEMPLATES = None


def load_dependencies():
    global PROCESSORS, TEMPLATES
    executable = shutil.which("ffmpeg")
    if executable is None:
        raise RuntimeError("FFmpeg executable is missing from PATH in this Python session.")
    # MoviePy and ffmpeg-python use the same installed executable.
    os.environ["IMAGEIO_FFMPEG_EXE"] = executable
    try:
        import cv2
        import ffmpeg
        from instagram_processor import InstagramProcessor
        from tiktok_processor import TikTokProcessor
    except ImportError as error:
        raise RuntimeError(
            "Dependency import failed. These unchanged files require MoviePy 1.x "
            "(moviepy==1.0.3), ffmpeg-python, NumPy and OpenCV. "
            f"Original error: {error}"
        ) from error
    if not all(hasattr(ffmpeg, attribute) for attribute in ("input", "output", "run")):
        raise RuntimeError("Install ffmpeg-python: the imported ffmpeg module is not the expected package.")
    cv2.setNumThreads(1)
    PROCESSORS = {"instagram": InstagramProcessor, "tiktok": TikTokProcessor}
    TEMPLATES = {}
    for platform, names in TEMPLATE_NAMES.items():
        templates = [cv2.imread(str(HERE / name), cv2.IMREAD_GRAYSCALE) for name in names]
        for name, template in zip(names, templates):
            if template is None:
                raise RuntimeError(f"Template could not be read: {HERE / name}")
        TEMPLATES[platform] = templates


def initialize_worker(cpu_queue):
    # One assigned CPU per process. FFmpeg child processes inherit this affinity.
    os.sched_setaffinity(0, {cpu_queue.get(timeout=30)})
    load_dependencies()


def signature(path):
    info = path.stat()
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns


def find_videos(root, scan_root):
    found = []

    def scan_error(error):
        raise error  # Do not silently omit unreadable subdirectories.

    # Scan only the requested subtree, but retain Party/Participant in outputs.
    for folder, directories, filenames in os.walk(scan_root, onerror=scan_error, followlinks=False):
        for name in directories:
            if (Path(folder) / name).is_symlink():
                raise ValueError(f"Unexpected symbolic-link folder in organised input: {Path(folder) / name}")
        directories.sort()
        for name in sorted(filenames):
            source = Path(folder) / name
            if source.suffix.lower() != ".mp4":
                continue
            if source.is_symlink() or not source.is_file():
                raise ValueError(f"Input must be a regular MP4 file: {source}")
            relative = source.relative_to(root)
            if len(relative.parts) != 5:
                raise ValueError(f"Expected Party/Participant/Date/Platform/video.mp4: {relative}")
            party, person, date, platform, filename = relative.parts
            if party not in {"Fidesz", "Tisza"} or person not in {"1", "2", "3", "4"}:
                raise ValueError(f"Unrecognised party or participant: {relative}")
            datetime.strptime(date, "%Y%m%d")
            if platform.lower() not in TEMPLATE_NAMES:
                raise ValueError(f"Unrecognised platform folder: {relative}")
            found.append((source, relative, platform.lower()))
    return found


def process_one(job):
    source = Path(job["source"])
    output = Path(job["output"])
    work = Path(job["work"])
    link = work / "input.mp4"
    default_output = work / "input"
    processor = None
    before = None
    row = {key: job[key] for key in ("source", "output", "log")}
    row.update(status="failed", clips=0, frames=0, expected_frames=0, note="")

    with open(job["log"], "x", encoding="utf-8", buffering=1) as log:
        with redirect_stdout(log), redirect_stderr(log):
            try:
                before = signature(source)
                if before[2] == 0:
                    raise ValueError("Input is an empty MP4.")
                print(f"Original: {source}\nSplits: {output}", flush=True)
                print(f"Worker PID: {os.getpid()}, CPU: {sorted(os.sched_getaffinity(0))}", flush=True)
                output.mkdir(parents=True, exist_ok=False)
                work.mkdir(parents=True, exist_ok=False)
                if Path(str(link).split(".mp4")[0]) != default_output:
                    raise ValueError("The output root cannot contain '.mp4' in a directory name.")
                link.symlink_to(source)

                cls = PROCESSORS[job["platform"]]
                # Retain the object even if its constructor fails, for cleanup.
                processor = cls.__new__(cls)
                cls.__init__(processor, str(link), *TEMPLATES[job["platform"]])
                processor.output_dir = str(output)  # Output routing only.
                processor.process_video()           # Original algorithm, unchanged.

                clips = list(output.glob("*.mp4"))
                if not clips or any(path.stat().st_size == 0 for path in clips):
                    raise RuntimeError("No non-empty clips, or at least one empty clip, was produced.")
                row["clips"] = len(clips)
                row["frames"] = processor.frame_counter
                row["expected_frames"] = processor.total_frames
                row["status"] = "ok"
                if processor.frame_counter < processor.total_frames:
                    row["status"] = "needs_review"
                    row["note"] = "Frame reading stopped before the reported frame count."
                elif len(clips) == 1:
                    row["note"] = "One clip produced; no split boundaries recorded."
            except Exception as error:
                row["status"] = "failed"
                row["note"] = f"{type(error).__name__}: {error}"
                traceback.print_exc()
                if getattr(error, "stderr", None):
                    stderr = error.stderr
                    print(stderr.decode("utf-8", errors="replace") if isinstance(stderr, bytes) else stderr)
            finally:
                if processor is not None:
                    for attr, method in (("cap", "release"), ("video", "close")):
                        resource = getattr(processor, attr, None)
                        if resource is not None:
                            try:
                                getattr(resource, method)()
                            except Exception:
                                traceback.print_exc()
                # Only remove OUR temporary link and OUR empty staging folders.
                if link.is_symlink():
                    link.unlink()
                for temporary_folder in (default_output, work):
                    try:
                        temporary_folder.rmdir()
                    except OSError:
                        pass
                try:
                    if before is not None and signature(source) != before:
                        raise RuntimeError("Source file metadata changed during processing.")
                except OSError as error:
                    row["status"] = "failed"
                    row["note"] += f" Source verification failed: {error}"
                except RuntimeError as error:
                    if row["status"] != "failed":
                        row["status"] = "needs_review"
                    row["note"] += f" {error}"
                print(json.dumps(row, indent=2), flush=True)
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=INPUT_ROOT)
    parser.add_argument("--scope", type=Path, default=INPUT_SCOPE,
                        help="Subfolder to process, relative to --input (default: Fidesz/1).")
    parser.add_argument("--output", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--workers", type=int, default=WORKERS)
    parser.add_argument("--check-only", action="store_true", help="Check inputs/dependencies without splitting.")
    args = parser.parse_args()
    source, destination = args.input.resolve(), args.output.resolve()
    if not source.is_dir():
        parser.error(f"Input directory not found: {source}")
    scoped_path = source / args.scope
    scan_root = scoped_path.resolve()
    if source != scan_root and source not in scan_root.parents:
        parser.error("The requested scope must stay inside the organised input directory.")
    if not scan_root.is_dir():
        parser.error(f"Requested test folder not found: {scan_root}")
    # A link in the scope path must not redirect Fidesz/1 to another participant.
    if scoped_path.absolute() != scan_root:
        parser.error("Use a direct scope path without symbolic links or '..' components.")
    if source == destination or source in destination.parents or destination in source.parents:
        parser.error("Input and output must be separate, non-overlapping directories.")
    if ".mp4" in str(destination):
        parser.error("The output root cannot contain '.mp4' in a directory name.")
    cpus = sorted(os.sched_getaffinity(0))
    if not 1 <= args.workers <= len(cpus):
        parser.error(f"Requested {args.workers} workers, but this process can access {len(cpus)} CPUs.")
    load_dependencies()
    videos = find_videos(source, scan_root)
    if not videos:
        parser.error(f"No MP4 files found in the requested test folder: {scan_root}")
    mapped = [str(relative.with_suffix("")) for _, relative, _ in videos]
    if len(mapped) != len(set(mapped)):
        parser.error("Two input filenames map to the same split folder. Resolve the filename collision first.")
    print(f"Dataset root: {source}\nONLY PROCESSING: {scan_root}\nOutput root: {destination}\nVideos: {len(videos)}\nWorkers: {args.workers}", flush=True)
    print("Dependencies and all six image templates loaded successfully.", flush=True)
    if args.check_only:
        print("Check finished. No splitting was started.", flush=True)
        return 0

    run_root = destination / (f"run_{datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:6]}")
    run_root.mkdir(parents=True, exist_ok=False)
    (run_root / "_logs").mkdir()
    (run_root / "_work").mkdir()
    print(f"THIS RUN: {run_root}", flush=True)
    jobs = []
    for index, (video, relative, platform) in enumerate(videos, 1):
        jobs.append({"source": str(video), "platform": platform,
                     "output": str(run_root / relative.with_suffix("")),
                     "work": str(run_root / "_work" / f"{index:05d}"),
                     "log": str(run_root / "_logs" / f"{index:05d}.log")})
    provenance = {"input": str(source), "scope": str(scan_root), "workers": args.workers, "jobs": jobs,
                  "processor_sha256": {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                                       for name in ("video_processor.py", "instagram_processor.py", "tiktok_processor.py")}}
    (run_root / "run_config.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    fields = ("source", "output", "status", "clips", "frames", "expected_frames", "note", "log")
    counts = Counter()
    report = run_root / "summary.csv"
    context = mp.get_context("spawn")
    cpu_queue = context.Queue()
    for cpu in cpus[:args.workers]:
        cpu_queue.put(cpu)
    with report.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        with ProcessPoolExecutor(max_workers=args.workers, mp_context=context,
                                 initializer=initialize_worker, initargs=(cpu_queue,)) as pool:
            pending = {pool.submit(process_one, job): job for job in jobs}
            finished = 0
            while pending:
                done, _ = wait(pending, timeout=30, return_when=FIRST_COMPLETED)
                if not done:
                    print(f"Running: {finished}/{len(jobs)} videos finished. Per-video logs: {run_root / '_logs'}", flush=True)
                for future in done:
                    job = pending.pop(future)
                    try:
                        row = future.result()
                    except Exception as error:
                        row = {key: job[key] for key in ("source", "output", "log")}
                        row.update(status="failed", clips=0, frames=0, expected_frames=0,
                                   note=f"Worker failed: {type(error).__name__}: {error}")
                    writer.writerow(row)
                    stream.flush()
                    counts[row["status"]] += 1
                    finished += 1
                    relative = Path(row["source"]).relative_to(source)
                    print(f"[{finished}/{len(jobs)}] {row['status'].upper()} | {relative} | {row['clips']} clips", flush=True)
                    if row["note"]:
                        print(f"  {row['note']}", flush=True)
    cpu_queue.close()
    cpu_queue.join_thread()
    print(f"\nFinished. OK: {counts['ok']}; needs review: {counts['needs_review']}; failed: {counts['failed']}", flush=True)
    print(f"Splits: {run_root}\nReport: {report}\nOriginal input folder: {source}", flush=True)
    return 1 if counts["failed"] or counts["needs_review"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
