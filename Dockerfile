FROM python:3.11-alpine

RUN apk add --no-cache tzdata

ENV TZ="Asia/Shanghai"

WORKDIR /app

COPY requirements.txt /app

# RUN pip install -U --no-cache-dir --require-hashes -r requirements.txt
RUN pip install -U --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
