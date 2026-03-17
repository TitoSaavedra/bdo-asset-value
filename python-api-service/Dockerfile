FROM python:3.11-slim

WORKDIR /app

COPY python-api-service/requirements-api.txt /app/requirements-api.txt
RUN pip install --no-cache-dir -r /app/requirements-api.txt

COPY python-api-service/ /app/

EXPOSE 8000

CMD ["python", "main.py"]
