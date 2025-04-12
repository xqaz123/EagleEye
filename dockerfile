FROM debian:bullseye

RUN apt-get clean && apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y locales
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
ENV TERM dumb
ENV PYTHONIOENCODING=utf-8

RUN apt update && apt upgrade -y
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y libgtk-3-dev libboost-all-dev build-essential cmake libffi-dev
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y firefox-esr
RUN apt-get install -y git python3 python3-pip python3-dev

RUN git clone https://github.com/xqaz123/EagleEye.git
RUN cd EagleEye && pip3 install -r requirements.txt
RUN pip3 install --upgrade beautifulsoup4 html5lib spry

WORKDIR EagleEye
ADD https://github.com/mozilla/geckodriver/releases/download/v0.36.0/geckodriver-v0.36.0-linux64.tar.gz /EagleEye/geckodriver.tar.gz
RUN tar -xvf geckodriver.tar.gz
RUN mv geckodriver /usr/bin/geckodriver
RUN chmod +x /usr/bin/geckodriver
RUN rm -r /EagleEye/known/
ENTRYPOINT bash /entry.sh

