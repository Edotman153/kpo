FROM python:3.8-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

#ENV PYTHONPATH="/app:${PYTHONPATH}"

#RUN pip install -e .

CMD ["python", "src/bot.py"]
