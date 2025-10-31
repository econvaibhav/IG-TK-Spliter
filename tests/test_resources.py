"""The wheel must contain the six original detector templates, byte for byte."""
import hashlib

import cv2
import numpy as np
import pytest

from spliter.video_processor import VideoProcessor

from .conftest import template_bytes


ORIGINAL_TEMPLATES = {
    ("instagram", "IG_comment_template.png"):
        "59bd0cc2e3695dfd1fb698a8e0220878c1da2d65d017ecb7a22ac08ebb14e730",
    ("instagram", "IG_heart_template.png"):
        "b43f97a486a496c6bb3f8849ce9112b6cbc1bc7a7d26030932161b141eee3c89",
    ("instagram", "IG_share_template.png"):
        "e64c47fa41735cc1ec6cd2a756e624f12177aab1c849fcdfc4335460c818a1c2",
    ("tiktok", "TK_heart_template.png"):
        "58046597ae5cd7415d207b484f1a7844796d7b59280f9f4b7616e5ef3f12e790",
    ("tiktok", "TK_save_template.png"):
        "797b5498f3ed8dae7dc2e8faa3490a53bb5842cf52e60e9c6be182cc9ab9ce25",
    ("tiktok", "TK_share_template.png"):
        "0df2e6702236a272f142b58ee30ca430a3e0de080feea0acf3fc6a448f802c24",
}


@pytest.mark.parametrize("resource,expected_hash", ORIGINAL_TEMPLATES.items())
def test_original_template_bytes_are_bundled(resource, expected_hash):
    raw = template_bytes(*resource)
    assert hashlib.sha256(raw).hexdigest() == expected_hash
    image = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_GRAYSCALE)
    assert image is not None and image.size > 0 and image.std() > 0


def test_template_matching_does_not_contaminate_later_matches():
    template = cv2.imdecode(np.frombuffer(
        template_bytes("tiktok", "TK_heart_template.png"), np.uint8
    ), cv2.IMREAD_GRAYSCALE)
    gray = np.zeros((960, 540), dtype=np.uint8)
    height, width = template.shape
    gray[200:200 + height, 450:450 + width] = template
    original = gray.copy()
    processor = object.__new__(VideoProcessor)
    processor.threshold = 0.85
    first = processor.match_template(gray, template)
    second = processor.match_template(gray, template)
    assert first == second
    # The first above-threshold match can precede the maximum-score pixel.
    assert first is not None and abs(first - 200) <= 2
    np.testing.assert_array_equal(gray, original)
    assert processor.match_template(gray[:1, :1], template) is None
