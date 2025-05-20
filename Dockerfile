FROM python:3.13-slim

RUN pip3 install poetry

ADD . /app
WORKDIR /app

# CMD ["poetry", "install"]
CMD ["bash"]
