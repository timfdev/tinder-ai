FROM python:3.11-slim

WORKDIR /code/messenger/app

COPY ../requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./messenger/app /code/messenger/app
COPY ./shared /code/shared

# Set the Python path for shared imports
ENV PYTHONPATH=/code

# Expose the application port
EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
