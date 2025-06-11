"""TikTok icon-position boundary candidates."""
from video_processor import VideoProcessor


class TikTokProcessor(VideoProcessor):
    platform = "tiktok"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.templates = self.load_templates(
            "TK_heart_template.png",
            "TK_share_template.png",
            "TK_save_template.png",
        )

    def process_frame(self, frame):
        gray = self.prepare_frame(frame, white_min=220)
        height = gray.shape[0]
        for template, divisor in zip(self.templates, (2, 1.6, 1.7)):
            y = self.match_template(gray, template)
            if y is not None and (
                y <= height / divisor or y > height - height / 6.3
            ):
                yield "tiktok_icons", 0.4
                break
