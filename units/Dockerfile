FROM python:3.8-slim

WORKDIR /units
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["pytest"]
