FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
        python3-pip \
        libgl1-mesa-glx \
        libglib2.0-0 \
        tesseract-ocr \
        wget \
        && rm -rf /var/lib/apt/lists/*

RUN cd /usr/share/tesseract-ocr/4.00/tessdata && \
       wget -q https://github.com/tesseract-ocr/tessdata/raw/master/spa.traineddata && \
       wget -q https://github.com/tesseract-ocr/tessdata/raw/master/eng.traineddata

RUN pip install pipenv

ADD bot/Pipfile* /bot/
RUN cd /bot && pipenv install --deploy --system --ignore-pipfile 
ADD meme_classifier /bot/meme_classifier
ADD template /bot/template
ADD notebooks/classifier-train_data.csv.pickle /bot/notebooks/classifier-train_data.csv.pickle
ADD bot /bot
CMD cd /bot && python3 main.py
