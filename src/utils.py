import cv2
import numpy as np

def draw_box_with_label(img, box, label, color=(0, 255, 0)):
    x1, y1, x2, y2 = map(int, box)
    cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
    ((tw, th), baseline) = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    cv2.rectangle(img, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
    cv2.putText(img, label, (x1 + 2, y1 - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)

def letterbox(image, new_shape=(1280, 720)):
    # Simple resize keeping aspect ratio by padding (for display only)
    h, w = image.shape[:2]
    r = min(new_shape[0]/w, new_shape[1]/h)
    nw, nh = int(w*r), int(h*r)
    resized = cv2.resize(image, (nw, nh))
    canvas = np.zeros((new_shape[1], new_shape[0], 3), dtype=np.uint8)
    canvas[:nh, :nw] = resized
    return canvas
