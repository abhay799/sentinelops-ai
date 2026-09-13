FROM python:3.14-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV SERVICE_PORT=8104

COPY services/requirements.txt /app/requirements.txt

RUN python -m pip install --no-cache-dir -r /app/requirements.txt

COPY services/inventory/app.py /app/app.py

EXPOSE 8104

HEALTHCHECK --interval=10s --timeout=3s --retries=5 --start-period=5s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8104/live')" || exit 1

CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8104"]
