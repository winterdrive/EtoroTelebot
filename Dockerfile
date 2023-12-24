# Use an official Python runtime as the base image
FROM python

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install the required packages listed in requirements.txt
RUN pip install --no-cache-dir -r requirements_linux.txt 

# Expose port 5000 to allow communication to/from server
EXPOSE 5000

# Copy the .env file to the container
COPY .env /app

# Set environment variables using values from the .env file
RUN set -a && \
    source .env && \
    set +a

# Run the command to start gunicorn
CMD ["gunicorn", "-w", "4", "--bind", "0.0.0.0:5000", "app:app"]
