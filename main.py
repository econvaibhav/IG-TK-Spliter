"""Split one Instagram or TikTok MP4 screen recording."""
import argparse
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Split a screen-recorded feed into candidate clips; keep the input."
    )
    parser.add_argument("input", type=Path, help="Unsplit .mp4 screen recording")
    parser.add_argument("--platform", required=True, type=str.lower,
                        choices=("instagram", "tiktok"))
    parser.add_argument("--output", type=Path,
                        help="New output directory (default: <input_stem>_splits)")
    parser.add_argument("--instagram-mode", choices=("both", "reels", "feed"),
                        default="both", help="Instagram checks to run (default: both)")
    parser.add_argument("--threshold", type=float, default=0.85,
                        help="Normalized template-match threshold (default: 0.85)")
    parser.add_argument("--templates-dir", type=Path,
                        help="Directory containing replacement icon PNG templates")
    parser.add_argument("--detect-only", action="store_true",
                        help="Write boundaries and report without exporting MP4 clips")
    args = parser.parse_args()

    if not 0 < args.threshold <= 1:
        parser.error("--threshold must be greater than 0 and at most 1.")
    if args.platform != "instagram" and args.instagram_mode != "both":
        parser.error("--instagram-mode applies only to Instagram.")

    try:
        # Lazy imports let --help work before video dependencies are installed.
        from instagram_processor import InstagramProcessor
        from tiktok_processor import TikTokProcessor

        processor_type = (InstagramProcessor if args.platform == "instagram"
                          else TikTokProcessor)
        options = dict(output_dir=args.output, threshold=args.threshold,
                       templates_dir=args.templates_dir)
        if args.platform == "instagram":
            options["mode"] = args.instagram_mode

        processor = processor_type(args.input, **options)
        result = processor.process_video(detect_only=args.detect_only)
        print(f"Status: {result['status']}")
        print(f"Intervals: {len(result['segments'])}")
        print(f"Output: {processor.output_dir}")
        return 0
    except ImportError as error:
        print(
            f"Missing dependency: {error}. "
            "Run python -m pip install -r requirements.txt",
            file=sys.stderr,
        )
        return 1
    except (OSError, ValueError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Stopped. The original recording is unchanged.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
