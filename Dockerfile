# Usa uma imagem oficial do Python leve (Slim) para o container ficar rápido
FROM python:3.10-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia o arquivo de requisitos primeiro para aproveitar o cache do Docker
COPY requirements.txt .

# Instala as dependências do projeto
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o resto dos arquivos do seu projeto para dentro do container
COPY . .

# Expõe a porta padrão do Streamlit (8501)
EXPOSE 8501

# Comando para verificar se o container está saudável (Healthcheck)
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# O comando que o Render vai rodar para iniciar seu app
ENTRYPOINT ["streamlit", "run", "brasileiro_serie_A.py", "--server.port=8501", "--server.address=0.0.0.0"]
