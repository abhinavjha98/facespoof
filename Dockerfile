# Use an official Python runtime as a parent image
FROM amd64/python:3.8.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV SKLEARN_ALLOW_DEPRECATED_SKLEARN_PACKAGE_INSTALL=True

# Set work directory
WORKDIR /usr/src/app

# Update and install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgl1-mesa-glx \  
    libglib2.0-0 \ 
    v4l-utils \          
    ffmpeg \              
    libsm6 \             
    libxext6 \            
    libxrender-dev \     
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install Python dependencies
COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . /usr/src/app/

# Expose the port that Django will run on
EXPOSE 8000

# Add permission for access to webcam (ensure /dev/video0 is mounted at runtime)
RUN apt-get update && apt-get install -y sudo
RUN useradd -ms /bin/bash appuser
RUN adduser appuser sudo
RUN echo 'appuser ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers
USER appuser

# Django and Gunicorn setup
CMD ["gunicorn", "--timeout", "500", "django_face_recognition.wsgi:application", "--bind",  "0.0.0.0:8000"]
