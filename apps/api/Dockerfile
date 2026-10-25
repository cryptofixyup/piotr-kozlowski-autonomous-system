FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY tests ./tests
RUN groupadd --gid 10001 appuser && useradd --uid 10001 --gid 10001 --create-home appuser
USER 10001:10001
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
