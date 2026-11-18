# Rebuilt SZL organ: stdlib-only sentra health service.
# The base image is digest-pinned; the tag records which library image it is.
FROM python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860
RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin organ
WORKDIR /app
COPY serve.py /app/serve.py
USER organ
EXPOSE 7860
CMD ["python", "/app/serve.py"]
