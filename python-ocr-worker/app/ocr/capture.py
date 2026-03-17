import mss
import numpy as np


def capture_region(region):

    monitor = {
        "left": region["x"],
        "top": region["y"],
        "width": region["width"],
        "height": region["height"],
    }

    with mss.mss() as sct:
        img = np.array(sct.grab(monitor))

    return img[:, :, :3]
