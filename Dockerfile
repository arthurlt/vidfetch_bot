FROM python:3.11-alpine

WORKDIR /opt/vidfetch_bot

COPY requirements.txt ./

RUN apk --no-cache add yt-dlp &&\
	pip install --no-cache-dir -r requirements.txt

COPY *.py .

CMD [ "python", "./main.py" ]