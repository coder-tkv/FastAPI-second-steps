FROM python:3.13.3

WORKDIR /app

COPY . .

RUN pip install -r requirments.txt

CMD ["python", "main.py"]