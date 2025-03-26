FROM python:3.10-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080
CMD ["streamlit", "run", "App Auth Streamlit.py", "--server.port=8080", "--server.address=0.0.0.0"]
