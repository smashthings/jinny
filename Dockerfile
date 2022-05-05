FROM smasherofallthings/base-image

RUN apt-get update && apt-get install -y python3 python3-pip && mkdir /jinny

COPY src/jinny /jinny

RUN cd /jinny && python3 -m pip install -r /jinny/requirements.txt

ENV PYTHONUNBUFFERED=TRUE
CMD ["/jinny/jinny"]
