# Use an official Python runtime as a parent image
FROM python:3.12-alpine
LABEL maintainer="nasjod"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH="/scripts:${PATH}"

# Install system dependencies
RUN apk update \
  && apk add --no-cache \
    gcc \
    g++ \
    musl-dev \
    libffi-dev \
    postgresql-dev \
    proj-dev \
    geos-dev \
    gdal-dev \
    binutils \
    bash

# Set work directory
RUN mkdir /app
WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy application code
COPY ./nasjod /app/

# Copy and make scripts executable
COPY ./scripts /scripts
RUN chmod +x /scripts/*

# Create necessary directories and set permissions
RUN mkdir -p /vol/web/media
RUN mkdir -p /vol/web/static
RUN adduser -D user
RUN chown -R user:user /vol/
RUN chmod -R 755 /vol/web
USER user

# Define volume
VOLUME ["/vol/web"]

# Set the entrypoint
ENTRYPOINT ["/script/entrypoint.sh"]
