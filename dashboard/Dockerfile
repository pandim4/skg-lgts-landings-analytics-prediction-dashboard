FROM python:3.9-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc default-libmysqlclient-dev pkg-config
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0"]
