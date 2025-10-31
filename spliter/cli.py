"""Split one Instagram or TikTok MP4 screen recording."""
import argparse
from pathlib import Path
import sys


PLATFORMS = {
    "instagram": "instagram", "ig": "instagram",
    "tiktok": "tiktok", "tk": "tiktok",
}


def parse_platform(value):
    """Accept either the platform name or its short alias."""
    try:
        return PLATFORMS[value.strip().lower()]
    except KeyError as error:
        raise argparse.ArgumentTypeError(
            "Choose instagram (ig) or tiktok (tk)."
        ) from error


def choose_platform(parser):
    """Offer a menu only at a terminal; batch jobs must select explicitly."""
    if not sys.stdin.isatty():
        parser.error(
            "--platform is required in a non-interactive session. "
            "Use --platform instagram (ig) or --platform tiktok (tk)."
        )
    print("Choose the recording platform:\n  1. Instagram\n  2. TikTok")
    while True:
        try:
            value = input("Platform [1/2]: ").strip().lower()
        except EOFError:
            parser.error("No platform selected. Pass --platform instagram or --platform tiktok.")
        value = {"1": "instagram", "2": "tiktok"}.get(value, value)
        try:
            return parse_platform(value)
        except argparse.ArgumentTypeError:
            print("Enter 1 / instagram / ig, or 2 / tiktok / tk.")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "doctor":
        from .doctor import main as doctor_main
        return doctor_main(argv[1:])

    from . import __version__
    parser = argparse.ArgumentParser(
        description="Split a screen-recorded feed into candidate clips; keep the input.",
        epilog="Run 'spliter doctor' to check the installation without a recording.",
    )
    parser.add_argument("--version", action="version", version=f"Spliter {__version__}")
    parser.add_argument("input", type=Path, help="Unsplit .mp4 screen recording")
    parser.add_argument("--platform", type=parse_platform,
                        metavar="{instagram,tiktok,ig,tk}",
                        help="Platform to split; omitted at a terminal, show a selection menu")
    parser.add_argument("--output", type=Path,
                        help="New output directory (default: <input_stem>_splits)")
    parser.add_argument("--instagram-mode", choices=("both", "reels", "feed"),
                        default="both", help="Instagram checks to run (default: both)")
    parser.add_argument("--threshold", type=float, default=0.85,
                        help="Normalized template-match threshold (default: 0.85)")
    parser.add_argument("--templates-dir", type=Path,
                        help="Platform-specific folder containing replacement icon PNG templates")
    parser.add_argument("--detect-only", action="store_true",
                        help="Write boundaries and report without exporting MP4 clips")
    args = parser.parse_args(argv)

    if not 0 < args.threshold <= 1:
        parser.error("--threshold must be greater than 0 and at most 1.")
    if args.platform is None:
        try:
            args.platform = choose_platform(parser)
        except KeyboardInterrupt:
            print("\nStopped. The original recording is unchanged.", file=sys.stderr)
            return 130
    if args.platform != "instagram" and args.instagram_mode != "both":
        parser.error("--instagram-mode applies only to Instagram.")

    try:
        # Lazy imports let --help work before video dependencies are installed.
        from .instagram_processor import InstagramProcessor
        from .tiktok_processor import TikTokProcessor

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
            "Install Spliter with its dependencies in this Python environment; "
            "see the README installation steps.",
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
