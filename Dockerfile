FROM python:3.12-slim

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy your app code
COPY . .

# Expose the application port
EXPOSE 8000

# Command to run on container start
CMD ["sh", "scripts/start.sh"]