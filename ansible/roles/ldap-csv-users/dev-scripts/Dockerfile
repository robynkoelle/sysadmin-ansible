FROM python:3.11-slim

WORKDIR /app
RUN pip install pyyaml pyOpenSSL
COPY . .

CMD ["python", "./generate_users.py"]

