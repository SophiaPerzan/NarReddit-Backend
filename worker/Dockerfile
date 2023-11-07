# Use an official Python runtime as a parent image
FROM python:3.11-bullseye

# Set the working directory in the container to /code
WORKDIR /code

# Add the current directory contents into the container at /code
ADD . /code

#Set shell to us UTF-8
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

#Install FFMPEG And Other Dependencies
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y ffmpeg && \
    apt-get install -y espeak libespeak1 libespeak-dev espeak-data && \
    apt-get install -y python3-dev

RUN pip install numpy

# Add the font files to the Docker image
COPY fonts/ /usr/share/fonts/

# Update the font cache
RUN fc-cache -f -v

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt