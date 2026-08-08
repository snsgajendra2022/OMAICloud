FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md /app/
COPY om_ai /app/om_ai
COPY configs /app/configs
RUN pip install --no-cache-dir .
EXPOSE 8080
CMD ["om-ai", "serve", "--host", "0.0.0.0", "--port", "8080"]
