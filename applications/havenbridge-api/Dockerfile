# Start with an official lightweight Python 3.12 image.
FROM python:3.12-slim

# Accept the HavenBridge application version during the Docker build.
# Official release builds override "unreleased" with the semantic version.
ARG APP_VERSION="unreleased"

# Make the build-time version available to the running application.
ENV APP_VERSION="${APP_VERSION}"

# Add OCI metadata for GitHub Container Registry.
LABEL org.opencontainers.image.source="https://github.com/brunobrunt/havenbridge-ha-service-platform" \
      org.opencontainers.image.description="FastAPI backend for the HavenBridge service inquiry and referral tracking platform"

# Prevent Python from creating .pyc files and ensure logs appear immediately.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Use /app as the working directory inside the container.
WORKDIR /app

# Copy the dependency list first so Docker can cache this layer.
COPY requirements.txt /app/requirements.txt

# Install the production Python dependencies.
RUN python -m pip install \
    --no-cache-dir \
    --requirement /app/requirements.txt

# Copy the HavenBridge application source code.
COPY app /app/app

# Create a non-root user for the API process.
RUN addgroup --system havenbridge && \
    adduser --system \
        --ingroup havenbridge \
        --home /home/havenbridge \
        havenbridge && \
    chown -R havenbridge:havenbridge /app

# Run the API as the non-root HavenBridge user.
USER havenbridge

# Document the port used by Uvicorn.
EXPOSE 8000

# Start the HavenBridge FastAPI application.
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
