FROM python:3.11.2

WORKDIR /app

COPY . /app

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

# Specify the command to run when the container starts
CMD [ "python", "main.py" ]
