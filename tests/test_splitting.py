"""End-to-end regressions against an installed package and its bundled icons."""
import json

import pytest

from spliter.instagram_processor import InstagramProcessor
from spliter.tiktok_processor import TikTokProcessor
from spliter.video_processor import VideoProcessor

from .conftest import assert_valid_clips, cli, file_hash, probe


@pytest.mark.parametrize("platform,processor_type,has_audio", [
    ("instagram", InstagramProcessor, True),
    ("tiktok", TikTokProcessor, False),
])
def test_real_icons_produce_two_clips(
    videos, tmp_path, platform, processor_type, has_audio
):
    source = videos[platform]
    original_hash = file_hash(source)
    options = {"mode": "reels"} if platform == "instagram" else {}
    processor = processor_type(source, output_dir=tmp_path / "clips", **options)
    report = processor.process_video()
    assert len(report["segments"]) == 2
    first = report["segments"][0]
    assert first["boundary_reason"] == f"{platform}_icons"
    assert first["end_seconds"] == pytest.approx(8 / 12 + 1.5 / 12, abs=1e-5)
    assert_valid_clips(processor.output_dir, report, audio=has_audio)
    assert file_hash(source) == original_hash


def test_no_match_silent_odd_dimensions(videos, tmp_path):
    source = videos["odd_silent"]
    original_hash = file_hash(source)
    processor = TikTokProcessor(source, output_dir=tmp_path / "clips")
    report = processor.process_video()
    assert report["status"] == "needs_review"
    assert len(report["segments"]) == 1
    assert_valid_clips(processor.output_dir, report, audio=False)
    video = next(item for item in probe(processor.output_dir / "part_0001.mp4")
                 ["streams"] if item["codec_type"] == "video")
    assert (video["width"], video["height"]) == (542, 962)
    assert file_hash(source) == original_hash


def test_cli_detect_only_and_existing_output_refusal(videos, tmp_path):
    source = videos["instagram"]
    original_hash = file_hash(source)
    output = tmp_path / "preview with spaces"
    cli(source, "--platform", "ig", "--instagram-mode", "reels",
        "--detect-only", "--output", output)
    report = json.loads((output / "report.json").read_text())
    assert len(report["segments"]) == 2
    assert all(not segment["exported"] for segment in report["segments"])
    assert not list(output.glob("*.mp4"))
    (output / "keep.txt").write_text("This file must survive unchanged.")
    before = {path.name: file_hash(path) for path in output.iterdir()}
    result = cli(source, "--platform", "ig", "--output", output, expected=1)
    assert "already exists" in result.stderr.lower()
    assert before == {path.name: file_hash(path) for path in output.iterdir()}
    assert file_hash(source) == original_hash


class NearEndCut(VideoProcessor):
    def process_frame(self, frame):
        if self.frames_read == 10:
            yield "near_end_regression", 0.4


@pytest.mark.parametrize("fixture,has_audio", [
    ("odd_silent", False), ("blank_audio", True),
])
def test_subframe_tail_does_not_become_empty_clip(
    videos, tmp_path, fixture, has_audio
):
    source = videos[fixture]
    original_hash = file_hash(source)
    processor = NearEndCut(source, output_dir=tmp_path / "clips")
    report = processor.process_video()
    assert len(report["segments"]) == 1
    assert_valid_clips(processor.output_dir, report, audio=has_audio)
    assert file_hash(source) == original_hash


def test_invalid_input_leaves_no_output(tmp_path):
    source = tmp_path / "invalid.mp4"
    source.write_bytes(b"not an MP4 file")
    original_hash = file_hash(source)
    output = tmp_path / "invalid_splits"
    cli(source, "--platform", "tk", expected=1)
    assert file_hash(source) == original_hash
    assert not output.exists()
    cli(tmp_path / "missing.mp4", "--platform", "tk", expected=1)


def test_invalid_options_fail_before_processing(videos, tmp_path):
    source = videos["odd_silent"]
    output = tmp_path / "unused"
    for arguments in (
        ("--platform", "tk", "--threshold", "nan"),
        ("--platform", "tk", "--instagram-mode", "feed"),
    ):
        cli(source, "--output", output, *arguments, expected=2)
        assert not output.exists()
