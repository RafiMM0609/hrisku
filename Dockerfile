FROM python:3.11.2-slim-buster
# FROM python:3.10-buster
# FROM python:3.11-buster

WORKDIR /usr/src/app

# install untuk pdfkit
RUN apt-get update && apt-get install -y wkhtmltopdf && rm -rf /var/lib/apt/lists/*
# RUN pip install deepface tf_keras
COPY ./requirements.txt .
COPY ./.env .
RUN pip install -r requirements.txt

EXPOSE 8000

COPY . .

# CMD [ "poetry", "run", "uvicorn", "main:app","--host", "0.0.0.0", "--port", "8000", "--reload"]
# CMD [ "uvicorn", "main:app","--host", "0.0.0.0", "--port", "8000", "--reload"]
CMD [ "uvicorn", "main:app","--host", "0.0.0.0", "--port", "8000", "--reload" ,"--log-config", "log_conf.json"]