"""7-Step pipeline"""

import LuxDataCollection as ldc
import cv2
import os
import numpy as np
import random as rd

"""1. Define Parameters For Paths"""
destination1_folder = 'Your Desired Path '
normalize_jpg = "normalized.JPG"
morphology_jpg = "morphology.JPG"
bw_jpg = "bw.JPG"
normalize_path = os.path.join(destination1_folder, normalize_jpg)
morphology_path = os.path.join(destination1_folder, morphology_jpg)
bw_path = os.path.join(destination1_folder, bw_jpg)

"""2. Select Image: Takes in an image, reads it and then splits into hsv
Filters out reflections with masking and then returns gray scaled image"""


def select_image(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        print("No Such Image exists")
        return None

    # HSV SPlit
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    # Thresholds: Reflections are low sat and high brightness
    sat_thresh = 10
    val_thresh = 240

    # Identify reflections
    reflection_mask = (s < sat_thresh) & (v > val_thresh)

    # Keep non-reflective pixels
    keep_mask = (~reflection_mask).astype(np.uint8) * 255

    filtered = cv2.bitwise_and(img, img, mask=keep_mask)

    gray = cv2.cvtColor(filtered, cv2.COLOR_BGR2GRAY)
    return gray


"""3. Normalize image illumination an denoise
Here uses histogram equalization for normalization
"""
def normalize_image(image):
    if image is None:
        return None
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl1 = clahe.apply(image)
    # fastNlMeansDenoising params: (src, dst, h, templateWindowSize, searchWindowSize)
    dst = cv2.fastNlMeansDenoising(cl1, None, h=10, templateWindowSize=7, searchWindowSize=21)
    return dst

"""4. Morphological cleanup, refine the image dust particles, and remove false positives"""
def morphology_cleanup(image):
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    opening = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
    closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)
    return closing

"""6. Adaptively Binarize the image for contours: Detect and Analyze shapes on surface
Takes in gray scaled image"""
def binarize_for_contours(image, thresh=20):
    if image is None:
        return None
    # Otsu Algorithm
    try:
        _, bw = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return bw
    except Exception:
        _, bw = cv2.threshold(image, thresh, 255, cv2.THRESH_BINARY)
        return bw

"""7. Calculate ratio of Total Dust Pixels/Total Surface Pixels"""
def calculate_ratio(image, mask_img):

    if image is None or mask_img is None:
        return None
    h, w = image.shape[:2]
    tot_pixel_count = h * w
    dust_pixel_count = np.count_nonzero(mask_img)
    p_over_t = dust_pixel_count / tot_pixel_count
    return p_over_t, dust_pixel_count, tot_pixel_count

# ---------- Main ---------- CLOSE EXCEL!!

if __name__ == "__main__":
    # Connect with board and calculate lux
    try:
        Apin = ldc.set_com("COM8")
        print("Board Communicated with")
        lux = ldc.collect_lux(Apin)
        print("Lux Calculated", lux)
    except Exception as e:
        print("Lux collection failed, continuing without lux. Error:", e)
        lux = None

    # Select Image + Initial processing + Reflection filtering
    raw_image = select_image("Cool+Dark.jpg")
    if raw_image is None:
        raise SystemExit("No input image. Exiting.")

    # Normalize and Denoise
    normalized_denoised = normalize_image(raw_image)

    # Apply Morphology
    morphology = morphology_cleanup(normalized_denoised)

    # Binarize for contours
    bw = binarize_for_contours(morphology)

    # Collect area ratio + print
    p_over_t, number_of_dust_pixels, total_pixels = calculate_ratio(raw_image, bw)

    print("Dust containing pixels / Total pixels:", p_over_t)
    print(number_of_dust_pixels, total_pixels)

    try:
        ldc.csv_data(lux, number_of_dust_pixels, p_over_t)
        print("CSV data collected")
    except Exception as e:
        print("ldc.csv_data failed:", e)

    # Save output images at all stages
    """Should create save paths for specific things"""
    cv2.imwrite(normalize_path, normalized_denoised)
    cv2.imwrite(bw_path, bw)
    cv2.imwrite(morphology_path, morphology)
    print("Filtered image saved")
    print("Done")
