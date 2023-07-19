# Use an official Python runtime as a parent image
FROM python:3-bullseye

# Set the working directory in the container to /app
WORKDIR /code

# Add the current directory contents into the container at /code
ADD . /code

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 5000

# Run app.py when the container launches
CMD ["python", "app.py"]