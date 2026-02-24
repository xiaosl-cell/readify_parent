FROM ghcr.io/astral-sh/uv:0.5.22 AS uv

FROM ccr-2vdh3abv-pub.cnc.bj.baidubce.com/paddlex/paddlex:paddlex3.0.1-paddlepaddle3.0.0-cpu

WORKDIR /app

COPY --from=uv /uv /uvx /usr/local/bin/

COPY requirements.txt ./
RUN uv pip install --system --no-cache -r requirements.txt

COPY . .

ENV OCR_HOST=0.0.0.0
ENV OCR_PORT=8090
ENV OCR_DEVICE=cpu
ENV OCR_LANGUAGE=ch
ENV OCR_USE_DOC_ORIENTATION_CLASSIFY=false
ENV OCR_USE_DOC_UNWARPING=false
ENV OCR_USE_TEXTLINE_ORIENTATION=false

EXPOSE 8090

CMD ["python", "main.py"]
