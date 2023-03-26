FROM python:3.11.2-alpine3.17

WORKDIR /usr/src/auto_racer

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY credentials.json ./

COPY . .

ENTRYPOINT ["python", "main.py"] 