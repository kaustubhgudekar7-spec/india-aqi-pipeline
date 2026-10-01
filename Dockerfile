FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["sh", "-c", "python -m pipeline.run && streamlit run dashboard/app.py --server.port=8501 --server.address=0.0.0.0"]
