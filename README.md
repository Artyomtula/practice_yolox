# Практика YOLOX

Проект обрабатывает видео с помощью Python, PyAV и YOLOX.

Скрипт сохраняет выбранные кадры из видео, находит на них объекты, обводит объекты прямоугольниками и окружностями, а также создаёт итоговое видео с выделенными объектами.

## Где что лежит

Основной скрипт:

```text
myscript.py
```

Входное видео лежит в корне проекта:

```text
input.ts
```

Папка с результатами:

```text
results/
```

В ней лежат сохранённые кадры, обработанные изображения и итоговое видео.

Исходные кадры:

```text
results/frame_100.jpg
results/frame_200.jpg
results/frame_234.jpg
```

Кадры с объектами, обведёнными прямоугольниками:

```text
results/frame_100_rect.jpg
results/frame_200_rect.jpg
results/frame_234_rect.jpg
```

Кадры с объектами, обведёнными окружностями:

```text
results/frame_100_circle.jpg
results/frame_200_circle.jpg
results/frame_234_circle.jpg
```

Итоговое обработанное видео:

```text
results/output_circles.mp4
```

Веса модели YOLOX должны лежать здесь:

```text
weights/yolox_s.pth
```

## Как запустить проект

Перейти в папку проекта:

```bash
cd practice_yolox
```

Создать виртуальное окружение:

```bash
python3.11 -m venv .venv
```

Активировать окружение:

```bash
source .venv/bin/activate
```

Обновить pip и setuptools:

```bash
python -m pip install --upgrade "pip<26" "setuptools<70" wheel
```

Установить PyTorch:

```bash
python -m pip install torch torchvision
```

Создать файл зависимостей без ONNX:

```bash
grep -v -E '^(onnx|onnx-simplifier)' requirements.txt > requirements-local.txt
```

Установить зависимости:

```bash
python -m pip install -r requirements-local.txt
python -m pip install av
```

Установить YOLOX:

```bash
python -m pip install -v -e . --no-build-isolation --no-deps
```

Создать папку для весов:

```bash
mkdir -p weights
```

Скачать веса YOLOX-s:

```bash
curl -L \
  https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1rc0/yolox_s.pth \
  -o weights/yolox_s.pth
```

## Запуск скрипта

Запуск для видео `input.ts`:

```bash
python myscript.py -i input.ts --frames=100,200,234
```

Параметр `-i` указывает путь к видеофайлу.

Параметр `--frames` указывает номера кадров, которые нужно сохранить и обработать.

Можно указать другие кадры:

```bash
python myscript.py -i input.ts --frames=50,100,150
```

Если видео называется иначе, например `video.mp4`, запуск будет таким:

```bash
python myscript.py -i video.mp4 --frames=100,200,234
```

## Что получится после запуска

После запуска все результаты будут лежать в папке:

```text
results/
```

Основные файлы результата:

```text
frame_100.jpg
frame_200.jpg
frame_234.jpg
frame_100_rect.jpg
frame_200_rect.jpg
frame_234_rect.jpg
frame_100_circle.jpg
frame_200_circle.jpg
frame_234_circle.jpg
output_circles.mp4
```

## Если 234 кадр не появился

Если файл `frame_234.jpg` не появился, значит в видео может быть меньше 234 кадров.

Проверить количество кадров можно так:

```bash
python - <<'PY'
import av

count = 0

with av.open("input.ts") as container:
    stream = container.streams.video[0]
    for frame in container.decode(stream):
        count += 1

print("Всего кадров:", count)
PY
```

Если кадров меньше 234, нужно использовать другое видео или указать существующие кадры:

```bash
python myscript.py -i input.ts --frames=100,150,200
```

## Возможное предупреждение на macOS

При запуске может появиться предупреждение про `AVFFrameReceiver` или `AVFAudioReceiver`.

Если скрипт продолжает работать, кадры сохраняются и видео создаётся, это предупреждение можно игнорировать.

## Для отчёта

В отчёт можно вставить:

1. Скриншот запуска скрипта в терминале.
2. Исходные кадры из папки `results`.
3. Кадры с прямоугольниками.
4. Кадры с окружностями.
5. Итоговое видео `results/output_circles.mp4`.
