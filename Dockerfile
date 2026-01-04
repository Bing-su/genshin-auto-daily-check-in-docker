FROM python:3.14-alpine

RUN apk add -U --no-cache tzdata tini

ENV TZ="Asia/Shanghai"

WORKDIR /app

COPY requirements.txt main.py /app/

RUN PYTHONDONTWRITEBYTECODE=1 pip install -U --no-cache-dir --require-hashes -r requirements.txt && \
    adduser -D lumine

USER lumine

ENTRYPOINT ["/sbin/tini", "--"]

CMD ["python", "main.py"]