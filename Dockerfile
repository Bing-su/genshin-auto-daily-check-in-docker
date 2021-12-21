FROM python:3.9-slim

ENV TZ="Asia/Seoul"

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]