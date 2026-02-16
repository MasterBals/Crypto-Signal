FROM python:3.12-slim
WORKDIR /app
COPY scheduler/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend-core/app/services/scheduler_job.py ./scheduler_job.py
CMD ["python", "scheduler_job.py"]
