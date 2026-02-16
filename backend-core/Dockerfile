FROM python:3.12-slim
WORKDIR /app
COPY backend-core/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend-core/app ./app
COPY config.json /app/config.json
ENV PYTHONPATH=/app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
