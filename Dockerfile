ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8

# Copy data for add-on
COPY run.sh ip100.py requirements.txt /

RUN apk add --no-cache python3 &&\
    python3 -m ensurepip &&\
    pip3 install -r requirements.txt

RUN chmod a+x /run.sh

CMD [ "/run.sh" ]