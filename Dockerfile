# Use an official Python runtime as a parent image
FROM python:3.8.12-slim AS builder

# Install system dependencies
RUN apt-get update -y && \
    apt-get upgrade -y && \
    apt-get install -y libpq-dev python-dev

# Create a non-root user
RUN useradd -ms /bin/bash aiplay

# Set the working directory
WORKDIR /app

# Copy the local code to the container
COPY . /app

# Change ownership of the /app directory to the new user
RUN chown -R aiplay /app

# Switch to the new user
USER aiplay

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Second stage: Use a smaller base image
FROM python:3.8.12-slim

# Copy only necessary files from the builder stage
COPY --from=builder /app /app

# Set the working directory
WORKDIR /app

# Expose the port the app runs on
EXPOSE 8000

# Specify the command to run on container start
CMD ["gunicorn", "base.wsgi", "--log-file", "-"]