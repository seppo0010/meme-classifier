from flask import Flask, request, redirect
import os
import cv2
from compare_images import compare_images
import urllib

app = Flask(__name__, static_folder='to_classify')
template_path = 'template'
toclassify_path = 'to_classify'
target_path = 'train'
templates = [(f, cv2.imread(os.path.join(template_path, f))) for f in os.listdir(template_path) if os.path.isfile(os.path.join(template_path, f))]

@app.route("/")
def index():
    onlyfiles = [f for f in os.listdir(toclassify_path) if os.path.isfile(os.path.join(toclassify_path, f)) and f != '.empty']
    if len(onlyfiles) == 0:
        return 'nothing to do here'
    path = onlyfiles[0]
    def get_score(template_image):
        score = compare_images(template_image, cv2.imread(os.path.join(toclassify_path, path)))
        return score['similarity'] - 2 * score['mse']
    similarities = [(template_name, get_score(template_image)) for (template_name, template_image) in templates]
    similarities = sorted(similarities, key=lambda s: -s[1])
    q = urllib.parse.quote
    return f'<img src="/to_classify/{path}" height=600 /><br><a href="classify?image={q(path)}&template=">None</a><br>' + '<br>'.join(f'<a href="classify?image={q(path)}&template={q(s[0])}">{s[0]}</a>' for s in similarities)

@app.route("/classify")
def classify():
    image = request.args['image']
    template = request.args['template']
    source = os.path.join(toclassify_path, image)
    if template == '':
        os.remove(source)
    else:
        if not os.path.isdir(os.path.join(target_path, template)):
            os.mkdir(os.path.join(target_path, template))
        os.rename(source, os.path.join(target_path, template, image))
    return redirect('/')

if __name__ == '__main__':
  app.run()
