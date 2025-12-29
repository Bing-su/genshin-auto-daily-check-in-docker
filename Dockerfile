FROM python:3.14-alpine AS builder

WORKDIR /install

COPY requirements.txt .

RUN PYTHONDONTWRITEBYTECODE=1 pip install --prefix=/install --no-cache-dir --require-hashes -r requirements.txt

FROM python:3.14-alpine

RUN apk add -U --no-cache tzdata tini && \
    adduser -D lumine

ENV TZ="Asia/Shanghai"

WORKDIR /app

COPY --from=builder /install /usr/local

COPY main.py .

USER lumine

ENTRYPOINT ["/sbin/tini", "--"]

CMD ["python", "main.py"]
