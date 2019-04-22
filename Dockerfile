FROM python:3.7

WORKDIR /usr/local/src/nosql1h19-report-stats

COPY src/requirements.txt .

RUN pip install -r requirements.txt

RUN python -m nltk.downloader stopwords punkt

COPY src/database ./database

COPY src/static ./static

COPY src/templates ./templates

COPY src/utils ./utils

COPY src/app.py .