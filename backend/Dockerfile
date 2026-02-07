FROM python:3.6-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
  && apt-get install -y --no-install-recommends curl build-essential libta-lib0 libta-lib-dev \
  && rm -rf /var/lib/apt/lists/*

ARG CRYPTOSIGNAL_REF=master

RUN curl -fsSL "https://github.com/CryptoSignal/Crypto-Signal/archive/refs/heads/${CRYPTOSIGNAL_REF}.zip" -o /tmp/crypto-signal.zip \
  && python -m zipfile -e /tmp/crypto-signal.zip /tmp \
  && mv "/tmp/Crypto-Signal-${CRYPTOSIGNAL_REF}"/* /app/ \
  && rm -rf /tmp/crypto-signal.zip "/tmp/Crypto-Signal-${CRYPTOSIGNAL_REF}"

RUN pip install --no-cache-dir -r app/requirements-step-1.txt \
  && pip install --no-cache-dir -r app/requirements-step-2.txt

EXPOSE 8886

CMD ["python", "app/backend_server.py"]
