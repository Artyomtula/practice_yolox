# Лаба 3: Docker + Python + YOLOX

Проект запускает обработку видео через Docker.

Скрипт читает видео через PyAV, сохраняет выбранные кадры, находит объекты с помощью YOLOX, обводит объекты прямоугольниками и окружностями, а также сохраняет итоговое видео с окружностями вокруг объектов.

## Где что лежит

Основной скрипт:

```text
src/myscript.py
```

Входное видео кладём сюда:

```text
input/myvideo.ts
```

Папка для результатов:

```text
output/
```

После запуска там появляются:

```text
output/frame_100.jpg
output/frame_200.jpg
output/frame_234.jpg

output/frame_100_rect.jpg
output/frame_200_rect.jpg
output/frame_234_rect.jpg

output/frame_100_circle.jpg
output/frame_200_circle.jpg
output/frame_234_circle.jpg

output/result.mp4
```

Где:

* `frame_100.jpg`, `frame_200.jpg`, `frame_234.jpg` — обычные кадры из видео;
* `*_rect.jpg` — кадры с объектами, обведёнными прямоугольниками;
* `*_circle.jpg` — кадры с объектами, обведёнными окружностями;
* `result.mp4` — итоговое видео, где объекты обведены окружностями.

## Что нужно установить

Нужно установить только:

```text
Docker
Docker Compose
```

Python и библиотеки руками ставить не нужно: они устанавливаются внутри Docker-образа.

## Быстрый запуск

Склонировать репозиторий:

```bash
git clone https://github.com/Artyomtula/practice_yolox.git
cd practice_yolox
```

Создать папки для входного видео и результатов:

```bash
mkdir -p input output
```

Положить видео в папку `input` и назвать его:

```text
myvideo.ts
```

То есть путь должен быть такой:

```text
input/myvideo.ts
```

Собрать и запустить проект через Docker Compose:

```bash
docker compose up --build
```

После завершения работы результаты будут в папке:

```text
output/
```

## Запуск через обычный Docker

Сначала собрать образ:

```bash
docker build -t python-yolox-app .
```

Потом запустить обработку:

```bash
docker run --rm \
  -v ./input:/app/input \
  -v ./output:/app/output \
  python-yolox-app \
  python src/myscript.py \
  -i input/myvideo.ts \
  --frames=100,200,234 \
  --output_dir output
```

## Запуск с другими кадрами

Например, если нужно сохранить и обработать кадры `120`, `130`, `140`:

```bash
docker run --rm \
  -v ./input:/app/input \
  -v ./output:/app/output \
  python-yolox-app \
  python src/myscript.py \
  -i input/myvideo.ts \
  --frames=120,130,140 \
  --output_dir output
```

Или через Docker Compose:

```bash
docker compose run --rm yolox-app \
  python src/myscript.py \
  -i input/myvideo.ts \
  --frames=120,130,140 \
  --output_dir output
```

## Проверка Docker

Проверить, что Docker работает:

```bash
docker run hello-world
```

Проверить Docker Compose:

```bash
docker compose version
```

## Если не появился кадр 234

Если файла нет:

```text
output/frame_234.jpg
```

значит в видео может быть меньше 234 кадров.

Можно запустить с другими кадрами:

```bash
docker compose run --rm yolox-app \
  python src/myscript.py \
  -i input/myvideo.ts \
  --frames=100,150,200 \
  --output_dir output
```

## Что писать в отчёте

В отчёт можно добавить:

1. Скриншот команды `docker run hello-world`.
2. Скриншот команды `docker compose up --build`.
3. Скриншот папки `output`.
4. Сохранённые кадры `frame_100.jpg`, `frame_200.jpg`, `frame_234.jpg`.
5. Кадры с прямоугольниками.
6. Кадры с окружностями.
7. Итоговое видео `output/result.mp4`.

## Кратко про работу программы

1. Видео открывается через PyAV.
2. Из видео сохраняются выбранные кадры.
3. YOLOX находит объекты на кадрах.
4. Объекты обводятся прямоугольниками.
5. По прямоугольнику вычисляется центр объекта.
6. По максимальной стороне прямоугольника строится окружность.
7. Всё видео обрабатывается покадрово.
8. Результат сохраняется в `output/result.mp4`.
