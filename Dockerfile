FROM python:3.12-slim

RUN pip3 install poetry

ADD . /app
WORKDIR /app
RUN rm poetry.lock

# CMD ["poetry", "install"]
CMD ["bash"]