FROM python:3.11-alpine

# firefox-esr doesnt work for this!
RUN apk update && apk upgrade
RUN apk add --no-cache sqlite firefox vim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy requirements list and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Initialize the SQLite database if it doesn't exist
RUN ls ./data | grep sql.db > /dev/null || cat schema.sql | sqlite3 ./data/sql.db

# Expose the port the app runs on
EXPOSE 5000

# Define environment variable to run Flask in development mode
# only applicable if doing "flask run". Otherwise, see override inside app.py
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=yukon-energy

# Run the Flask app
#CMD ["flask", "run"]   # Dont do it this way, or the setup "__main__" code wont run!
CMD ["python3", "app.py"]
