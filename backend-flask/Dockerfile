FROM 646349589143.dkr.ecr.us-east-2.amazonaws.com/cruddur-python:3.10-slim-buster

WORKDIR /backend-flask

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1


EXPOSE ${PORT}
ENTRYPOINT [ "sh", "./start.sh" ]