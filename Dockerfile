FROM --platform=linux/amd64 python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ffmpeg \
    curl \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-docker.txt .

RUN python -m pip install --upgrade "pip<26" "setuptools<70" wheel

RUN python -m pip install \
    torch==2.5.1+cpu \
    torchvision==0.20.1+cpu \
    --index-url https://download.pytorch.org/whl/cpu

RUN python -m pip install -r requirements-docker.txt

COPY . .

RUN python -m pip install -v -e . --no-build-isolation --no-deps

RUN mkdir -p weights \
    && curl -L \
    https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1rc0/yolox_s.pth \
    -o weights/yolox_s.pth

CMD ["python", "src/myscript.py", "-i", "input/myvideo.ts", "--frames=100,200,234", "--output_dir", "output"]