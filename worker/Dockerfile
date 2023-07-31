# Use an official Python runtime as a parent image
FROM python:3-bullseye

# Set the working directory in the container to /code
WORKDIR /code

# Add the current directory contents into the container at /code
ADD . /code

#Install FFMPEG
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y ffmpeg

# Add the font files to the Docker image
COPY fonts/ /usr/share/fonts/

# Update the font cache
RUN fc-cache -f -v

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt