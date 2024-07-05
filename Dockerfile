FROM python:3.12-alpine

RUN apk add -U --no-cache tzdata

ENV TZ="Asia/Shanghai"

WORKDIR /app

COPY requirements.txt /app

RUN pip install -U --no-cache-dir --require-hashes -r requirements.txt

COPY . .

CMD ["python", "main.py"]
