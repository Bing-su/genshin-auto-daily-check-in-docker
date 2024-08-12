FROM python:3.12-alpine

RUN apk add -U --no-cache tzdata

ENV TZ="Asia/Shanghai"

WORKDIR /app

COPY requirements.lock main.py /app/

RUN PYTHONDONTWRITEBYTECODE=1 pip install -U --no-cache-dir --require-hashes -r requirements.lock

CMD ["python", "main.py"]
