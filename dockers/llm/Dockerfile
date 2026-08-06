FROM dustynv/vllm:r36.4-cu129-24.04
#FROM dustynv/vllm:0.8.5-r36.4.0-cu128-24.04

RUN pip install --no-cache-dir fastapi uvicorn pydantic --index-url https://pypi.org/simple
RUN pip uninstall -y transformers

RUN pip install --no-cache-dir \
    git+https://github.com/huggingface/transformers.git

RUN python3 -c "import vllm; print(vllm.__version__)"
EXPOSE 8090
#RUN python3 -c "import transformers; print(transformers.__version__)"
#RUN pip install --upgrade --no-cache-dir  transformers --index-url https://pypi.org/simple



