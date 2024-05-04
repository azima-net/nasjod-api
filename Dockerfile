# Use an official Python runtime as a parent image
FROM python:3.12-slim
LABEL maintainer="nasjod"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH="/scripts:${PATH}"

# Set work directory
RUN  mkdir /app
WORKDIR /app

# Install system dependencies
RUN apt-get update \
  && apt-get install -y gcc libpq-dev \
  && apt-get install -y binutils libproj-dev gdal-bin libgdal-dev libgeos-dev postgresql-client \
  && apt-get clean

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY ./nasjod /app/

COPY ./scripts /scripts
RUN chmod +x /scripts/*

RUN mkdir -p /vol/web/media
RUN mkdir -p /vol/web/static
RUN adduser --disabled-password --gecos "" user
RUN chown -R user:user /vol/
RUN chmod -R 755 /vol/web
USER user

VOLUME [ "/vol/web" ]
CMD ["entrypoint.sh"]
