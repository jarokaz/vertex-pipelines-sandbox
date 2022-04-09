FROM python:3.7.13

RUN pip install absl-py

WORKDIR /source

ADD task.py ./

ENTRYPOINT ["python", "task.py"]