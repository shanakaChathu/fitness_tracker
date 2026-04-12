FROM python:3.11-slim

WORKDIR /app

# Step 1: Install required Python libraries
# Copied before source so Docker can cache this layer — only reruns when pyproject.toml changes
COPY pyproject.toml .
RUN pip install --no-cache-dir \
    "mcp[cli]>=1.0.0" \
    "httpx>=0.27.0" \
    "python-dotenv>=1.0.0"

# Step 2: Copy source code and install the package itself (no deps re-download)
COPY src/ src/
RUN pip install --no-cache-dir --no-deps .

EXPOSE 8080

CMD ["python", "-m", "whoop_mcp.server"]
