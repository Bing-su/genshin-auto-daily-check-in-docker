FROM python:3.14-alpine

RUN apk add -U --no-cache tzdata

ENV TZ="Asia/Shanghai"

WORKDIR /app

COPY requirements.txt main.py /app/

RUN PYTHONDONTWRITEBYTECODE=1 pip install -U --no-cache-dir --require-hashes -r requirements.txt

CMD ["python", "main.py"]
