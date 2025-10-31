"""Check dependencies, bundled templates and a temporary H.264/AAC export."""
import argparse
from importlib.resources import files
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


TEMPLATES = {
    "instagram": (
        "IG_heart_template.png", "IG_comment_template.png", "IG_share_template.png",
    ),
    "tiktok": (
        "TK_heart_template.png", "TK_share_template.png", "TK_save_template.png",
    ),
}


def run_command(command):
    """Keep an unhealthy external binary from hanging the environment check."""
    result = subprocess.run(
        command, capture_output=True, text=True, timeout=30, check=False,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(detail[-1600:] or f"Command exited with {result.returncode}.")
    return result.stdout


def check_export(ffmpeg, ffprobe):
    """Encode and inspect a disposable clip; never open a user's recording."""
    with tempfile.TemporaryDirectory(prefix="spliter-doctor-") as temporary:
        clip = Path(temporary) / "check.mp4"
        run_command([
            ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-n",
            "-f", "lavfi", "-i", "color=c=black:s=32x32:r=10:d=0.2",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=0.2",
            "-t", "0.2", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-pix_fmt", "yuv420p", "-fps_mode", "vfr",
            "-c:a", "aac", "-b:a", "192k", "-video_track_timescale", "90000",
            "-movflags", "+faststart", str(clip),
        ])
        metadata = json.loads(run_command([
            ffprobe, "-v", "error", "-count_packets", "-show_entries",
            "stream=codec_type,codec_name,nb_read_packets", "-of", "json", str(clip),
        ]))
        streams = metadata.get("streams", [])
        for kind, codec in (("video", "h264"), ("audio", "aac")):
            valid = False
            for stream in streams:
                if stream.get("codec_type") == kind and stream.get("codec_name") == codec:
                    try:
                        valid = int(stream.get("nb_read_packets", 0)) > 0
                    except (ValueError, TypeError):
                        pass
                    if valid:
                        break
            if not valid:
                raise RuntimeError(f"The test clip contains no readable {codec} {kind} packets.")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="spliter doctor",
        description="Check dependencies, all six templates and H.264/AAC export without an input video.",
    )
    parser.parse_args(argv)
    failed = False
    numpy = None
    cv2 = None

    try:
        import numpy
        print(f"OK   NumPy {numpy.__version__}")
    except (ImportError, OSError, RuntimeError, ValueError) as error:
        print(f"FAIL NumPy: {error}")
        failed = True
    try:
        import cv2
        print(f"OK   OpenCV {cv2.__version__}")
    except (ImportError, OSError, RuntimeError, ValueError) as error:
        print(f"FAIL OpenCV: {error}")
        failed = True

    if numpy is not None and cv2 is not None:
        checked = 0
        for platform, filenames in TEMPLATES.items():
            for filename in filenames:
                try:
                    resource = files("spliter").joinpath("templates").joinpath(platform).joinpath(filename)
                    data = resource.read_bytes()
                    template = cv2.imdecode(
                        numpy.frombuffer(data, numpy.uint8), cv2.IMREAD_GRAYSCALE,
                    )
                    if template is None or template.size == 0 or float(template.std()) < 1e-6:
                        raise ValueError("PNG is unreadable or has no contrast")
                    checked += 1
                except (OSError, ValueError, cv2.error) as error:
                    print(f"FAIL Template {platform}/{filename}: {error}")
                    failed = True
        if checked == 6:
            print("OK   Templates: 6 readable PNGs")
    else:
        print("SKIP Template decoding: NumPy and OpenCV are required")

    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    for name, executable in (("FFmpeg", ffmpeg), ("ffprobe", ffprobe)):
        if executable:
            print(f"OK   {name}: {executable}")
        else:
            print(f"FAIL {name}: not found on PATH")
            failed = True
    if ffmpeg and ffprobe:
        try:
            check_export(ffmpeg, ffprobe)
            print("OK   H.264/AAC export: encoded and verified a temporary clip")
        except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
            print(f"FAIL H.264/AAC export: {error}")
            print("     Install an FFmpeg build with libx264 and AAC; see the README.")
            failed = True
        except KeyboardInterrupt:
            print("\nStopped. Temporary check files were removed.", file=sys.stderr)
            return 130
    else:
        print("SKIP H.264/AAC export: FFmpeg and ffprobe are required")

    print("Installation check failed." if failed else "Ready to split recordings.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
