# Pull Python base image
FROM python:3.8-alpine

# Copy requirements file to container
COPY ./requirements.txt /app/requirements.txt

# Set the working directory in the container
WORKDIR /app

# Install dependencies
RUN pip install -r requirements.txt

# Copy the application code to the container
COPY . /app

# Command to run the application
CMD ["python3", "app.py"]