FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PLAYWRIGHT_BROWSERS_PATH=/opt/playwright
RUN pip install --no-cache-dir playwright==1.58.0 requests python-dotenv \
    && python -m playwright install --with-deps chromium
WORKDIR /workspace
CMD ["python", "bancochile_web_server.py", "--host", "0.0.0.0", "--port", "8030"]
