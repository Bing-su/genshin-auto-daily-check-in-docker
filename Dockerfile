FROM python:3.14-alpine

RUN apk add -U --no-cache tzdata tini

ENV TZ="Asia/Shanghai"

WORKDIR /app

COPY pylock.toml main.py /app/

RUN PYTHONDONTWRITEBYTECODE=1 pip install -U --no-cache-dir -r pylock.toml && \
    adduser -D lumine

USER lumine

ENTRYPOINT ["/sbin/tini", "--"]

CMD ["python", "main.py"]
