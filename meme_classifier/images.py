import os
import pickle
try:
    from PIL import Image
except ImportError:
    import Image
import numpy as np
import pandas as pd
import cv2
import pytesseract
from skimage.metrics import structural_similarity, normalized_root_mse, adapted_rand_error, hausdorff_distance, peak_signal_noise_ratio
from matplotlib import cm
import pathlib

base_path = pathlib.Path(__file__).parent.absolute()
template_path = os.path.join(base_path, '..', 'template')
templates = [(1+i, f, cv2.imread(os.path.join(template_path, f))) for i, f in enumerate(os.listdir(template_path)) if os.path.isfile(os.path.join(template_path, f))]
csv_path = 'train_data.csv'
classifier = pickle.load(open(os.path.join(base_path, '..', f'notebooks/classifier-{csv_path}.pickle'), "rb"))

columns = []
for t in templates:
    columns.append(t[1] + '_similarity')
    columns.append(t[1] + '_mse')
    columns.append(t[1] + '_compare_hist')

def get_row(after):
    cols = []
    for _, template_name, template_image in templates:
        comparison = compare_images(template_image, after)
        cols.extend((comparison['similarity'], comparison['mse'], comparison['compare_hist']))
    return cols

def compare_images(before, after):
    after = cv2.resize(after, [300, 300])
    before = cv2.resize(before, [300, 300])
    # Convert images to grayscale
    before_gray = cv2.cvtColor(before, cv2.COLOR_BGR2GRAY)
    after_gray = cv2.cvtColor(after, cv2.COLOR_BGR2GRAY)

    # Compute SSIM between two images
    (score, diff) = structural_similarity(before_gray, after_gray, full=True)
    # The diff image contains the actual image differences between the two images
    # and is represented as a floating point data type in the range [0,1]
    # so we must convert the array to 8-bit unsigned integers in the range
    # [0,255] before we can use it with OpenCV
    diff = (diff * 255).astype("uint8")

    # Threshold the difference image, followed by finding contours to
    # obtain the regions of the two input images that differ
    thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    contours = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = contours[0] if len(contours) == 2 else contours[1]

    mask = np.zeros(before.shape, dtype='uint8')
    filled_after = after.copy()

    for c in contours:
        area = cv2.contourArea(c)
        if area > 40:
            x,y,w,h = cv2.boundingRect(c)
            cv2.rectangle(before, (x, y), (x + w, y + h), (36,255,12), 2)
            cv2.rectangle(after, (x, y), (x + w, y + h), (36,255,12), 2)
            cv2.drawContours(mask, [c], 0, (0,255,0), -1)
            cv2.drawContours(filled_after, [c], 0, (0,255,0), -1)

    score2 = normalized_root_mse(before, after)

    # https://theailearner.com/2019/08/13/comparing-histograms-using-opencv-python/
    img1_hsv = cv2.cvtColor(before, cv2.COLOR_BGR2HSV)
    img2_hsv = cv2.cvtColor(after, cv2.COLOR_BGR2HSV)
    hist_img1 = cv2.calcHist([img1_hsv], [0,1], None, [180,256], [0,180,0,256])
    cv2.normalize(hist_img1, hist_img1, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX);
    hist_img2 = cv2.calcHist([img2_hsv], [0,1], None, [180,256], [0,180,0,256])
    cv2.normalize(hist_img2, hist_img2, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX);
    compare_hist = cv2.compareHist(hist_img1, hist_img2, cv2.HISTCMP_BHATTACHARYYA)

    # remove the following since htey are slow and added no value to the model
    # are, prec, rec = adapted_rand_error(before, after)
    # hausdorff_d = hausdorff_distance(before, after)
    # psnr = peak_signal_noise_ratio(before, after)
    return {
        'similarity': score,
        'mse': score2,
        'compare_hist': compare_hist,
        # 'adapted_rand_error_are': are,
        # 'adapted_rand_error_prec': prec,
        # 'adapted_rand_error_rec': rec,
        # 'hausdorff_distance': hausdorff_d,
        # 'psnr': psnr,
    }

def process_image(content):
    nparr = np.frombuffer(content.read(), np.uint8)

    img_np = cv2.imdecode(nparr, flags=1)
    # cv2.imwrite('cv.jpg', img_np)

    data = get_row(img_np)
    df = pd.DataFrame([data], columns=columns)
    proba = classifier.predict_proba(df)[0]
    index = np.argmax(proba)
    val = np.argmax(proba)

    content.seek(0)
    pil_image = Image.open(content)
    # pil_image.save("pil.jpg", "JPEG")

    text = '\n'.join((
        pytesseract.image_to_string(pil_image, lang='eng'),
        pytesseract.image_to_string(pil_image, lang='spa'),
    ))
    return int(index), text
