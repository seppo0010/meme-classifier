import pandas as pd
import cv2
import sys
import os
from compare_images import compare_images

template_path = 'template'
templates = [(1+i, f, cv2.imread(os.path.join(template_path, f))) for i, f in enumerate(os.listdir(template_path)) if os.path.isfile(os.path.join(template_path, f))]

def get_row(path, label):
    cols = []
    after = cv2.imread(path)
    for label, template_name, template_image in templates:
        comparison = compare_images(template_image, after)
        cols.extend((comparison['similarity'], comparison['mse']))
    cols.append(label)
    return cols

rows = []
for root, dirs, files in os.walk('train'):
    if root == 'train':
        continue
    if os.path.basename(root) == 'garbage':
        label = 0
    else:
        label = [t[0] for t in templates if os.path.basename(root) == t[1]][0]

    for f in files:
        rows.append(get_row(os.path.join(root, f), label))

columns = []
for t in templates:
    columns.append(t[1] + '_similarity')
    columns.append(t[1] + '_mse')
columns.append('label')
df = pd.DataFrame(rows, columns=columns)
df.to_csv('train_data.csv')
