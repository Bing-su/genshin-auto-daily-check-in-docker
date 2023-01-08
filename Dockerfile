FROM python:3.11-slim

ENV TZ="Asia/Shanghai"

WORKDIR /app

COPY requirements.txt /app

RUN pip install -U --no-cache-dir --require-hashes -r requirements.txt

COPY . .

CMD ["python", "main.py"]
