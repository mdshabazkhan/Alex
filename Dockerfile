FROM python:3.11-slim

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Install python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and configurations
COPY config/ /app/config/
COPY matrix/ /app/matrix/
COPY jarvis/ /app/jarvis/
COPY hermes/ /app/hermes/
COPY tools/ /app/tools/
COPY evals/ /app/evals/
COPY Alex_Safety_Guardrails.md /app/
COPY docker-entrypoint.sh /app/

# Ensure entrypoint is executable
RUN chmod +x /app/docker-entrypoint.sh

# Expose ports:
# 8700: Matrix Supervisor & Gateway / Web UI
# 8642: Hermes Gateway
EXPOSE 8700 8642

ENTRYPOINT ["/app/docker-entrypoint.sh"]
