FROM python:3.7

RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 9DA31620334BD75D9DCB49F368818C72E52529D4

RUN echo "deb http://repo.mongodb.org/apt/debian stretch/mongodb-org/4.0 main" | tee /etc/apt/sources.list.d/mongodb-org-4.0.list

RUN apt-get update

RUN apt-get install mongodb-org-tools -y

WORKDIR /usr/local/src/nosql1h19-report-stats

COPY src/requirements.txt .

RUN pip install -r requirements.txt

RUN python -m nltk.downloader stopwords punkt

COPY src/database ./database

COPY src/static ./static

COPY src/templates ./templates

COPY src/utils ./utils

COPY src/app.py .