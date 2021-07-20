FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
        python3-pip \
        && rm -rf /var/lib/apt/lists/*

RUN pip install pipenv

ADD tweet/Pipfile* /tweet/
RUN cd /tweet && pipenv install --deploy --system --ignore-pipfile 
ADD meme_classifier /tweet/meme_classifier
ADD tweet /tweet
CMD cd /tweet/run.sh
