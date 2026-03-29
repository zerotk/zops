FROM python:3.13-slim

RUN pip3 install uv

ADD . /app
WORKDIR /app

# CMD ["uv", "sync"]
CMD ["bash"]
