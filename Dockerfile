# Use uma imagem Python como base
FROM python:3.11-slim

# Instale dependências do sistema
RUN apt-get update && apt-get install -y build-essential

# Copie os arquivos do projeto
WORKDIR /st_iDivi
COPY . /st_iDivi

# Instale dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Exponha a porta usada pelo Streamlit
EXPOSE 8080

# Comando para iniciar o Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
