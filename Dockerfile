FROM ubuntu:16.04
MAINTAINER Nathan Bowness, nathanbowness@gmail.com

RUN apt-get update && apt-get install -y \
		python3.5 \
		python3-dev \
		python3-setuptools \
		python3-pip \
		gcc \
		bash \
		docker \
		git

COPY requirements.txt /
RUN pip install -r requirements.txt

RUN docker build https://github.com/OLC-LOC-Bioinformatics/geneSipprV2.git#master:sipprverse

EXPOSE 8000
ENV C_FORCE_ROOT 1
ENTRYPOINT /bin/bash /app/init.sh

