# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install dependencies
#RUN pip install --no-cache-dir -r requirements.txt

# Initialize the SQLite database if it doesn't exist
#RUN ls | grep sql.db > /dev/null || cat schema.sql | sqlite3 sql.db

# Expose the port the app runs on
#EXPOSE 5000

# Define environment variable to run Flask in development mode
#ENV FLASK_APP=app.py
#ENV FLASK_RUN_HOST=0.0.0.0

# Run the Flask app
#CMD ["flask", "run"]

CMD ["tail", "-f", "/dev/null"]

