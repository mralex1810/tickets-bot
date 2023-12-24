FROM python:alpine

RUN apk add --update --no-cache build-base postgresql-dev python3-dev musl-dev libffi-dev && \
    pip3 install --upgrade pip && \
    pip3 install python-telegram-bot==13.15 && \
    pip3 install peewee pyyaml urllib3==1.26.18 && \
    rm -r /root/.cache && \
    apk del build-base 

ENV PYTHONPATH=/app/
WORKDIR /app/

EXPOSE 8080

COPY . /app/
RUN mkdir -p /app/tickets

CMD ["python3", "bot.py"]
