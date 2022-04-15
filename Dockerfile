FROM python:3.10-slim

ENV TZ="Asia/Seoul"

WORKDIR /app

COPY pyproject.toml poetry.lock /app/

RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev && \
    yes | poetry cache clear . --all

COPY . .

CMD ["python", "main.py"]
