"""Short generated recordings; no downloaded or private test media."""
import hashlib
from importlib.resources import files
import json
from pathlib import Path
import subprocess
import sys

import cv2
import numpy as np
import pytest


def run_command(arguments, expected=0, **kwargs):
    result = subprocess.run(
        [str(arg) for arg in arguments], capture_output=True, timeout=30, **kwargs
    )
    assert result.returncode == expected, (
        f"Command: {arguments}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    return result


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def template_bytes(platform, filename):
    return files("spliter").joinpath("templates", platform, filename).read_bytes()


def probe(path):
    result = run_command([
        "ffprobe", "-v", "error", "-show_entries",
        "stream=codec_type,width,height,nb_frames:format=duration",
        "-of", "json", path,
    ], text=True)
    return json.loads(result.stdout)


def cli(*arguments, expected=0):
    return run_command(
        [sys.executable, "-m", "spliter", *arguments], expected, text=True,
        input="",  # An omitted platform must fail rather than wait for input.
    )


def blank(width=540, height=960):
    return np.zeros((height, width, 3), dtype=np.uint8)


def icon_frame(platform, y):
    frame = blank()
    prefix = "IG" if platform == "instagram" else "TK"
    icon = cv2.imdecode(
        np.frombuffer(template_bytes(platform, f"{prefix}_heart_template.png"),
                      dtype=np.uint8), cv2.IMREAD_COLOR,
    )
    assert icon is not None
    height, width = icon.shape[:2]
    frame[y:y + height, 450:450 + width] = icon
    return frame


def make_video(path, frames, audio=False, fps=12):
    height, width = frames[0].shape[:2]
    command = [
        "ffmpeg", "-hide_banner", "-v", "error", "-nostdin", "-n",
        "-f", "rawvideo", "-pixel_format", "bgr24", "-video_size",
        f"{width}x{height}", "-framerate", str(fps), "-i", "pipe:0",
    ]
    if audio:
        command += [
            "-f", "lavfi", "-i",
            f"sine=frequency=440:sample_rate=48000:duration={len(frames) / fps}",
        ]
    command += [
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "10",
        "-pix_fmt", "yuv444p", "-c:a", "aac", path,
    ]
    run_command(command, input=b"".join(frame.tobytes() for frame in frames))
    return path


@pytest.fixture(scope="session", autouse=True)
def bounded_opencv_threads():
    previous = cv2.getNumThreads()
    cv2.setNumThreads(2)
    yield
    cv2.setNumThreads(previous)


@pytest.fixture(scope="session")
def videos(tmp_path_factory):
    folder = tmp_path_factory.mktemp("generated recordings")
    result = {}
    for platform, usual_y, audio in (
        ("instagram", 500, True), ("tiktok", 650, False),
    ):
        frames = [icon_frame(platform, 200 if index == 8 else usual_y)
                  for index in range(16)]
        result[platform] = make_video(
            folder / f"{platform} transition.mp4", frames, audio=audio
        )
    result["odd_silent"] = make_video(
        folder / "odd silent.mp4", [blank(541, 961)] * 12
    )
    result["blank_audio"] = make_video(
        folder / "blank audio.mp4", [blank()] * 12, audio=True
    )
    return result


def assert_valid_clips(output, report, audio):
    """Check interval coverage and actual decodable video, not file existence."""
    previous_end = 0.0
    for segment in report["segments"]:
        assert segment["start_seconds"] == pytest.approx(previous_end)
        assert segment["end_seconds"] > segment["start_seconds"]
        previous_end = segment["end_seconds"]
        path = output / segment["file"]
        streams = probe(path)["streams"]
        video = next(item for item in streams if item["codec_type"] == "video")
        assert int(video["nb_frames"]) > 0
        assert any(item["codec_type"] == "audio" for item in streams) is audio
        result = run_command([
            "ffmpeg", "-v", "error", "-nostdin", "-i", path, "-f", "null", "-",
        ], text=True)
        assert result.stderr == ""
    assert previous_end == pytest.approx(report["duration_seconds"])
    assert json.loads((output / "report.json").read_text()) == report
    assert (output / "segments.csv").is_file()
    assert not list(output.glob(".*.pending.mp4"))
