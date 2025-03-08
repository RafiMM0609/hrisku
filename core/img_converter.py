import os
import cv2
import base64


def img_to_base64(local_path: str) -> str:
    img = cv2.imread(local_path, cv2.IMREAD_UNCHANGED)
    _, file_extension = os.path.splitext(local_path)
    if file_extension == "png":  # Prevent remove background non png file
        if img.shape[2] == 4:
            # make mask of where the transparent bits are
            trans_mask = img[:, :, 3] == 0

            # replace areas of transparency with white and not transparent
            img[trans_mask] = [255, 255, 255, 255]

            # new img without alpha channel...
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    jpg_img = cv2.imencode(".jpg", img)
    b64_string = base64.b64encode(jpg_img[1]).decode("utf-8")
    return b64_string
