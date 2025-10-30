"""Instagram icon and feed-layout boundary candidates."""
import cv2
from .video_processor import VideoProcessor


class InstagramProcessor(VideoProcessor):
    platform = "instagram"

    def __init__(self, *args, mode="both", **kwargs):
        if mode not in {"both", "reels", "feed"}:
            raise ValueError("Instagram mode must be both, reels or feed.")
        super().__init__(*args, **kwargs)
        self.mode = mode
        self.templates = (
            self.load_templates(
                "IG_heart_template.png",
                "IG_comment_template.png",
                "IG_share_template.png",
            )
            if mode != "feed" else []
        )

    def process_frame(self, frame):
        # The caller updates the shared last cut before the generator resumes.
        if self.mode != "feed":
            gray = self.prepare_frame(frame, white_min=230, fill_contours=True)
            height = gray.shape[0]
            coordinates = [self.match_template(gray, t) for t in self.templates]
            if any(
                y is not None and 90 < y < 860
                and (y < height / 3 or y > height - height / 6.3)
                for y in coordinates
            ):
                yield "instagram_icons", 0.4

        if self.mode != "reels":
            gray = self.prepare_frame(frame, white_min=250, fill_contours=True)
            gray = cv2.dilate(gray, None, iterations=2)
            gray = cv2.erode(gray, None, iterations=2)
            height, width = gray.shape
            cv2.line(gray, (0, 0), (0, height - 1), 255, 2)
            cv2.line(gray, (width - 1, 0), (width - 1, height - 1), 255, 2)
            gray = cv2.bitwise_not(gray)
            contours, _ = cv2.findContours(
                gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            for contour in contours:
                perimeter = cv2.arcLength(contour, True)
                corners = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
                if len(corners) != 4:
                    continue
                _, y, w, h = cv2.boundingRect(corners)
                if w > width - 20 and 45 <= y <= 120 and 150 <= h <= 200:
                    yield "instagram_layout", 1.0
                    break
