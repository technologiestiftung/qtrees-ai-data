FROM python:3.10-alpine

WORKDIR /

COPY scripts/* ./

RUN pip install --no-cache-dir boto3

ENTRYPOINT ["python"]