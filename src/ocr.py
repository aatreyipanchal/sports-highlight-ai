import easyocr
import numpy as np
import re

class JerseyOCR:
    def __init__(self, languages=('en',)):
        self.reader = easyocr.Reader(languages, gpu=False)
        self.digits_re = re.compile(r"\d+")

    def read_digits(self, image_bgr):
        # Expect roughly upright digits; caller should crop jersey region
        image_rgb = image_bgr[:, :, ::-1]
        results = self.reader.readtext(image_rgb, detail=1, paragraph=False)
        best = None
        best_conf = 0.0
        for (bbox, text, conf) in results:
            text = ''.join(ch for ch in text if ch.isdigit())
            if not text:
                continue
            if conf > best_conf:
                best, best_conf = text, conf
        return best, best_conf
