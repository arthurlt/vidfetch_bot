FROM python:3.11-alpine

WORKDIR /opt/vidfetch_bot

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY *.py .

CMD [ "python", "./main.py" ]