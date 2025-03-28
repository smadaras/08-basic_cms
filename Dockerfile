# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
# RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -r requirements.txt

# Make port 8500 available to the world outside this container
EXPOSE 8501


# Define environment variable
ENV STREAMLIT_SERVER_PORT=8501

# Run app.py when the container launches
CMD ["streamlit", "run", "app.py"]

# How to build a docker image
# sudo docker build -t cms-python .