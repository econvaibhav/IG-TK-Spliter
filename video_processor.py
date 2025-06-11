"""Shared MP4 reading, template matching, boundary checks and FFmpeg export."""
import csv
from fractions import Fraction
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys

import cv2
import numpy as np


class VideoProcessor:
    analysis_height = 960
    platform = "unknown"

    def __init__(self, video_url, output_dir=None, threshold=0.85,
                 templates_dir=None):
        self.input_path = Path(video_url).expanduser().resolve()
        if not self.input_path.is_file() or self.input_path.suffix.lower() != ".mp4":
            raise ValueError("Input must be an existing .mp4 file.")
        if self.input_path.stat().st_size == 0:
            raise ValueError("The input MP4 is empty.")
        if not math.isfinite(threshold) or not 0 < threshold <= 1:
            raise ValueError("Template threshold must be in (0, 1].")

        self.threshold = threshold
        self.output_dir = (
            Path(output_dir).expanduser().resolve() if output_dir else
            self.input_path.with_name(self.input_path.stem + "_splits")
        )
        if self.output_dir.exists():
            raise ValueError(
                f"Output already exists: {self.output_dir}. Choose a new --output."
            )

        self.templates_dir = (
            Path(templates_dir).expanduser().resolve() if templates_dir else
            Path(__file__).resolve().parent
        )
        self.ffmpeg = shutil.which("ffmpeg")
        self.ffprobe = shutil.which("ffprobe")
        if not self.ffmpeg or not self.ffprobe:
            raise RuntimeError("Install FFmpeg with ffprobe and put both on PATH.")

        self.warnings = []
        self.segments = []
        self.templates = []
        self.frames_read = 0
        self.fps = 0.0
        self.duration = 0.0
        self.last_cut = 0.0

    @staticmethod
    def positive_number(value):
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        return number if math.isfinite(number) and number > 0 else None

    def warn(self, message):
        if message not in self.warnings:
            self.warnings.append(message)
            print(f"Warning: {message}", file=sys.stderr)

    def probe(self):
        result = subprocess.run(
            [
                self.ffprobe, "-v", "error", "-select_streams", "v:0",
                "-show_entries",
                "stream=duration,duration_ts,time_base,start_time,"
                "avg_frame_rate,r_frame_rate:format=duration,start_time",
                "-of", "json", str(self.input_path),
            ],
            capture_output=True, text=True,
        )
        if result.returncode:
            raise RuntimeError(
                "ffprobe could not read the MP4: " + result.stderr.strip()
            )

        metadata = json.loads(result.stdout)
        streams = metadata.get("streams", [])
        if not streams:
            raise ValueError("The MP4 contains no video stream.")
        stream = streams[0]
        format_info = metadata.get("format", {})

        def finite_or_zero(value):
            try:
                value = float(value)
                return value if math.isfinite(value) else 0.0
            except (TypeError, ValueError):
                return 0.0

        self.video_offset = max(
            0.0,
            finite_or_zero(stream.get("start_time"))
            - finite_or_zero(format_info.get("start_time")),
        )
        duration = self.positive_number(stream.get("duration"))
        if duration is None:
            try:
                duration = self.positive_number(
                    float(stream["duration_ts"])
                    * float(Fraction(stream["time_base"]))
                )
            except (KeyError, ValueError, TypeError, ZeroDivisionError):
                pass

        if duration is None:
            raise ValueError(
                "The video stream has no usable duration; "
                "repair or remux the MP4 first."
            )
        duration += self.video_offset

        fps = None
        for field in ("avg_frame_rate", "r_frame_rate"):
            try:
                fps = self.positive_number(Fraction(stream.get(field, "0/1")))
            except (ValueError, ZeroDivisionError):
                continue
            if fps:
                break
        return duration, fps

    def load_templates(self, *filenames):
        result = []
        for filename in filenames:
            path = self.templates_dir / filename
            if not path.is_file():
                raise ValueError(f"Missing template: {path}")
            template = cv2.imdecode(
                np.frombuffer(path.read_bytes(), np.uint8),
                cv2.IMREAD_GRAYSCALE,
            )
            if template is None or template.size == 0:
                raise ValueError(f"Unreadable template: {path}")
            if float(template.std()) < 1e-6:
                raise ValueError(f"Template has no contrast: {path}")
            result.append(template)
        return result

    @staticmethod
    def prepare_frame(frame, white_min, fill_contours=False):
        mask = cv2.inRange(frame, (white_min,) * 3, (255,) * 3)
        masked = cv2.bitwise_and(frame, frame, mask=mask)
        gray = cv2.cvtColor(masked, cv2.COLOR_BGR2GRAY)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel, iterations=1)
        if fill_contours:
            contours, _ = cv2.findContours(
                gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            for contour in contours:
                if cv2.contourArea(contour) > 50:
                    corners = cv2.approxPolyDP(
                        contour, 0.02 * cv2.arcLength(contour, True), True
                    )
                    cv2.drawContours(gray, [corners], 0, 255, -1)
        return gray

    def match_template(self, gray, template):
        height, width = template.shape
        if height > gray.shape[0] or width > gray.shape[1]:
            return None
        # Each template sees the same image; matching never draws onto gray.
        scores = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
        ys, xs = np.where(np.isfinite(scores) & (scores >= self.threshold))
        valid = np.flatnonzero(xs > 360)
        return int(ys[valid[0]]) if valid.size else None

    def process_frame(self, frame):
        raise NotImplementedError

    def export_segment(self, start, end, destination):
        temporary = destination.with_name("." + destination.stem + ".pending.mp4")
        command = [
            self.ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-n",
            "-ss", f"{start:.9f}", "-i", str(self.input_path),
            "-t", f"{end - start:.9f}",
            "-map", "0:v:0", "-map", "0:a:0?", "-sn", "-dn",
            "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-pix_fmt", "yuv420p", "-fps_mode", "vfr",
            "-c:a", "aac", "-b:a", "192k",
            "-video_track_timescale", "90000", "-movflags", "+faststart",
            str(temporary),
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode:
                raise RuntimeError("FFmpeg export failed: " + result.stderr.strip())
            if not temporary.is_file() or temporary.stat().st_size == 0:
                raise RuntimeError("FFmpeg produced no clip.")
            if destination.exists():
                raise RuntimeError(f"Refusing to overwrite {destination}")
            temporary.replace(destination)
        finally:
            # Only remove this run's unfinished output, never the input.
            temporary.unlink(missing_ok=True)

    def finish_interval(self, end, reason, detect_only):
        end = min(max(float(end), 0.0), self.duration)
        if end - self.last_cut <= 1e-9:
            return

        filename = f"part_{len(self.segments) + 1:04d}.mp4"
        if not detect_only:
            self.export_segment(
                self.last_cut, end, self.output_dir / filename
            )
        self.segments.append({
            "file": filename,
            "start_seconds": self.last_cut,
            "end_seconds": end,
            "duration_seconds": end - self.last_cut,
            "boundary_reason": reason,
            "exported": not detect_only,
        })
        print(f"{filename}: {self.last_cut:.3f} - {end:.3f} s ({reason})")
        self.last_cut = end

    def save_report(self, status, detect_only, error=None):
        report = {
            "input": str(self.input_path),
            "platform": self.platform,
            "instagram_mode": getattr(self, "mode", None),
            "status": status,
            "error": error,
            "detect_only": detect_only,
            "duration_seconds": self.duration,
            "fps": self.fps,
            "frames_read": self.frames_read,
            "threshold": self.threshold,
            "analysis_height": self.analysis_height,
            "warnings": self.warnings,
            "segments": self.segments,
        }
        fields = [
            "file", "start_seconds", "end_seconds", "duration_seconds",
            "boundary_reason", "exported",
        ]
        with (self.output_dir / "segments.csv").open(
            "w", newline="", encoding="utf-8"
        ) as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(self.segments)

        (self.output_dir / "report.json").write_text(
            json.dumps(report, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        return report

    def process_video(self, detect_only=False):
        self.duration, probed_fps = self.probe()
        cap = cv2.VideoCapture(str(self.input_path))
        if not cap.isOpened():
            cap.release()
            raise RuntimeError("OpenCV could not open the video stream.")

        output_created = False
        try:
            self.fps = probed_fps or self.positive_number(
                cap.get(cv2.CAP_PROP_FPS)
            )
            if not self.fps:
                raise ValueError("The recording has no usable positive frame rate.")

            ok, frame = cap.read()
            if not ok or frame is None or frame.size == 0:
                raise RuntimeError("The recording contains no decodable video frames.")

            height, width = frame.shape[:2]
            analysis_width = int(self.analysis_height * width / height)
            if analysis_width < 1:
                raise ValueError("Invalid frame dimensions.")
            if self.templates and analysis_width <= (
                360 + min(t.shape[1] for t in self.templates)
            ):
                raise ValueError("The recording is too narrow for the x > 360 icon rule.")
            if any(
                t.shape[0] > self.analysis_height or t.shape[1] > analysis_width
                for t in self.templates
            ):
                raise ValueError("A template is larger than the resized analysis frame.")

            self.output_dir.mkdir(parents=True, exist_ok=False)
            output_created = True
            raw_first = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            origin = (
                raw_first if math.isfinite(raw_first) and raw_first >= 0 else 0.0
            )
            previous_time = None

            while ok:
                raw_time = (
                    cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                    - origin + self.video_offset
                )
                if previous_time is None:
                    timestamp = self.video_offset
                elif math.isfinite(raw_time) and raw_time > previous_time:
                    timestamp = raw_time
                else:
                    timestamp = max(
                        self.video_offset + self.frames_read / self.fps,
                        previous_time + 1 / self.fps,
                    )
                    self.warn(
                        "OpenCV timestamps are missing or non-increasing; "
                        "using FPS timing for affected frames."
                    )

                if timestamp > self.duration + max(0.5, 3 / self.fps):
                    raise RuntimeError(
                        "Frame timestamps extend beyond the probed duration."
                    )
                previous_time = timestamp
                resized = cv2.resize(
                    frame, (analysis_width, self.analysis_height)
                )
                candidate_time = min(
                    timestamp + 1.5 / self.fps, self.duration
                )
                for reason, minimum_gap in self.process_frame(resized):
                    if candidate_time - self.last_cut > minimum_gap:
                        self.finish_interval(candidate_time, reason, detect_only)

                self.frames_read += 1
                ok, frame = cap.read()
                if ok and (frame is None or frame.size == 0):
                    raise RuntimeError(
                        "OpenCV returned an empty frame during decoding."
                    )

            if (
                self.duration - (previous_time + 1 / self.fps)
                > max(0.5, 3 / self.fps)
            ):
                raise RuntimeError(
                    "Decoding stopped well before the reported end; completed "
                    "clips are partial results. Check or repair this recording."
                )

            if not self.segments:
                self.warn(
                    "No boundary matched; the result is one whole-recording interval."
                )
            self.finish_interval(self.duration, "end_of_recording", detect_only)
            status = "needs_review" if self.warnings else "completed"
            return self.save_report(status, detect_only)
        except BaseException as error:
            if output_created:
                self.save_report(
                    "failed", detect_only, str(error) or type(error).__name__
                )
            raise
        finally:
            cap.release()
