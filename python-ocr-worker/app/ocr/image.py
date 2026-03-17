import cv2
import numpy as np


def upscale(img: np.ndarray, scale: int = 3) -> np.ndarray:
    h, w = img.shape[:2]
    return cv2.resize(img, (w * scale, h * scale), interpolation=cv2.INTER_CUBIC)


def to_gray(img: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def bright_text(img: np.ndarray) -> np.ndarray:
    gray = to_gray(upscale(img))
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    _, thresh = cv2.threshold(blur, 150, 255, cv2.THRESH_BINARY)
    return thresh


def warm_text(img: np.ndarray) -> np.ndarray:
    up = upscale(img)
    hsv = cv2.cvtColor(up, cv2.COLOR_BGR2HSV)
    lower = np.array([10, 40, 120])
    upper = np.array([40, 255, 255])
    mask = cv2.inRange(hsv, lower, upper)
    kernel = np.ones((2, 2), np.uint8)
    return cv2.dilate(mask, kernel, iterations=1)



def cream_to_bw(img):
    img_resized = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    hsv = cv2.cvtColor(img_resized, cv2.COLOR_BGR2HSV)
    lower_val = np.array([0, 0, 180])
    upper_val = np.array([60, 60, 255])
    mask = cv2.inRange(hsv, lower_val, upper_val)
    
    return mask