FROM python:3.8

RUN mkdir -p /home/bybit-profit-loss-sheet2
WORKDIR /home/bybit-profit-loss-sheet2

COPY requirements.txt /home/bybit-profit-loss-sheet2

RUN pip install -r /home/bybit-profit-loss-sheet2/requirements.txt

COPY . /home/bybit-profit-loss-sheet2