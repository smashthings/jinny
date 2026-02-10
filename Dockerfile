FROM smasherofallthings/base-python:amd64-latest

RUN mkdir /jinny

COPY pyproject.toml uv.lock /jinny
RUN cd /jinny && uv sync --active --no-install-project

COPY src/jinny /jinny
RUN  chmod a+x /jinny/jinny.py

ENV PYTHONUNBUFFERED=TRUE
CMD ["/jinny/jinny.py"]
