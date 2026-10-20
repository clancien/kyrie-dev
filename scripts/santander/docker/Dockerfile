FROM python:3.12-slim
WORKDIR /app
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && playwright install --with-deps --no-shell chromium && chmod -R a+rX /ms-playwright
COPY . .
CMD ["python", "santander_web_server.py", "--port", "8031"]
