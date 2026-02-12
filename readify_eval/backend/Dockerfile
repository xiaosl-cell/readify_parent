FROM python:3.11-slim
WORKDIR /app

RUN pip install uv -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY requirements.txt .
RUN uv pip install --system --no-cache torch --index-url https://download.pytorch.org/whl/cpu
RUN uv pip install --system --no-cache -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --extra-index-url https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match

COPY . .

EXPOSE 8082
CMD ["sh", "-c", "alembic upgrade head && python run.py"]
