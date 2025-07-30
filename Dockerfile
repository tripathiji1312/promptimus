# Step 1: Use an official Python runtime as a parent image
# We use 'slim' to keep the image size smaller
FROM python:3.11-slim

# Step 2: Set the working directory inside the container
WORKDIR /app

# Step 3: Copy the requirements file first to leverage Docker's layer caching
# This way, dependencies are only re-installed if requirements.txt changes
COPY requirements.txt .

# Step 4: Install the Python dependencies
# --no-cache-dir keeps the image lean
RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Copy the rest of your application's code into the container
# This includes agent.py, the 'data/', 'logs/', and adapter folders
COPY . .

# Step 6: Define the entry point for the container.
# This makes the container act like an executable for your agent.py script.
# Arguments passed to 'docker run' will be appended to this command.
ENTRYPOINT ["python", "agent.py"]