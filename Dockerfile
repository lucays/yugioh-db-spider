FROM python:3.8-slim-buster

RUN sed -i "s@http://deb.debian.org@http://mirrors.aliyun.com@g" /etc/apt/sources.list && \
    cat /etc/apt/sources.list && \
    rm -Rf /var/lib/apt/lists/* && \
    apt-get update -y && apt-get upgrade -y && apt-get install -y gcc gconf-service libasound2 libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 libglib2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 ca-certificates fonts-liberation libappindicator1 libnss3 lsb-release xdg-utils wget
WORKDIR /
COPY . .
RUN pip3 install -r requirements.txt
RUN pyppeteer-install
RUN rm -rf .git/
