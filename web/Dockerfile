FROM python:3.9
ENV PYTHONUNBUFFERED=1
RUN mkdir /sea_battle
WORKDIR /sea_battle
COPY requirements.txt /sea_battle/
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . /sea_battle/