FROM python:3.11-slim

WORKDIR /app

COPY service_app.py /app/service_app.py

ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["python", "/app/service_app.py"]
