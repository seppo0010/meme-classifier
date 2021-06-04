import cv2
import sys
from compare_images import compare_images

path_before = sys.argv[1]
before = cv2.imread(path_before)
for path_after in sys.argv[2:]:
    after = cv2.imread(path_after)
    res = compare_images(before, after)
    res2 = compare_images(after, before)
    print(f'{path_before},{path_after},{res["similarity"]+res2["similarity"]},{res["mse"]+res2["mse"]}')
