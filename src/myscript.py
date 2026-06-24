import argparse
from pathlib import Path

import av
import cv2
import torch

from yolox.data.data_augment import preproc
from yolox.exp import get_exp
from yolox.utils import postprocess


def parse_frames(frames_text):
    return [int(frame.strip()) for frame in frames_text.split(",") if frame.strip()]


def frame_to_bgr(frame):
    image_rgb = frame.to_ndarray(format="rgb24")
    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    return image_bgr


def load_yolox(weights_path):
    exp = get_exp(None, "yolox-s")

    exp.test_size = (640, 640)
    exp.test_conf = 0.25
    exp.nmsthre = 0.45

    model = exp.get_model()
    model.eval()

    checkpoint = torch.load(weights_path, map_location="cpu", weights_only=False)
    model.load_state_dict(checkpoint["model"])

    return model, exp


def detect_objects(model, exp, image_bgr):
    height, width = image_bgr.shape[:2]

    image, ratio = preproc(image_bgr, exp.test_size)
    image = torch.from_numpy(image).unsqueeze(0).float()

    with torch.no_grad():
        output = model(image)
        output = postprocess(
            output,
            exp.num_classes,
            exp.test_conf,
            exp.nmsthre,
            class_agnostic=True,
        )

    if output[0] is None:
        return []

    detections = output[0].cpu().numpy()
    boxes = detections[:, 0:4] / ratio

    result = []

    for box in boxes:
        x1, y1, x2, y2 = box.astype(int)

        x1 = max(0, min(x1, width - 1))
        y1 = max(0, min(y1, height - 1))
        x2 = max(0, min(x2, width - 1))
        y2 = max(0, min(y2, height - 1))

        if x2 > x1 and y2 > y1:
            result.append((x1, y1, x2, y2))

    return result


def draw_rectangles(image_bgr, boxes):
    result = image_bgr.copy()

    for x1, y1, x2, y2 in boxes:
        cv2.rectangle(
            result,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2,
        )

    return result


def draw_circles(image_bgr, boxes):
    result = image_bgr.copy()

    for x1, y1, x2, y2 in boxes:
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2

        box_width = x2 - x1
        box_height = y2 - y1
        radius = max(box_width, box_height) // 2

        cv2.circle(
            result,
            (center_x, center_y),
            radius,
            (0, 0, 255),
            2,
        )

    return result


def save_selected_frames(video_path, frame_numbers, output_dir, model, exp):
    needed_frames = set(frame_numbers)
    saved_frames = set()

    with av.open(video_path) as container:
        stream = container.streams.video[0]

        for frame_number, frame in enumerate(container.decode(stream), start=1):
            if frame_number in needed_frames:
                image_bgr = frame_to_bgr(frame)

                original_path = output_dir / f"frame_{frame_number}.jpg"
                cv2.imwrite(str(original_path), image_bgr)

                boxes = detect_objects(model, exp, image_bgr)

                image_rect = draw_rectangles(image_bgr, boxes)
                image_circle = draw_circles(image_bgr, boxes)

                rect_path = output_dir / f"frame_{frame_number}_rect.jpg"
                circle_path = output_dir / f"frame_{frame_number}_circle.jpg"

                cv2.imwrite(str(rect_path), image_rect)
                cv2.imwrite(str(circle_path), image_circle)

                saved_frames.add(frame_number)

                print(f"Сохранён кадр {frame_number}")
                print(f"Найдено объектов: {len(boxes)}")

            if frame_number >= max(frame_numbers):
                break

    for frame_number in frame_numbers:
        if frame_number not in saved_frames:
            print(f"Кадр {frame_number} не найден в видео")


def get_fps(stream):
    if stream.average_rate is not None:
        return float(stream.average_rate)

    return 25.0


def process_video(video_path, output_video_path, model, exp):
    with av.open(video_path) as container:
        stream = container.streams.video[0]
        fps = get_fps(stream)

        writer = None

        for frame_number, frame in enumerate(container.decode(stream), start=1):
            image_bgr = frame_to_bgr(frame)

            boxes = detect_objects(model, exp, image_bgr)
            result = draw_circles(image_bgr, boxes)

            if writer is None:
                height, width = result.shape[:2]
                fourcc = getattr(cv2, "VideoWriter_fourcc")(*"mp4v")

                writer = cv2.VideoWriter(
                    str(output_video_path),
                    fourcc,
                    fps,
                    (width, height),
                )

            writer.write(result)

            if frame_number % 30 == 0:
                print(f"Обработано кадров: {frame_number}")

        if writer is not None:
            writer.release()

    print(f"Видео сохранено: {output_video_path}")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Путь к входному видео",
    )

    parser.add_argument(
        "--frames",
        default="100,200,234",
        help="Номера кадров через запятую",
    )

    parser.add_argument(
        "--output_dir",
        default="output",
        help="Папка для сохранения результатов",
    )

    parser.add_argument(
        "--weights",
        default="weights/yolox_s.pth",
        help="Путь к весам YOLOX",
    )

    args = parser.parse_args()

    video_path = Path(args.input)
    output_dir = Path(args.output_dir)
    weights_path = Path(args.weights)

    output_dir.mkdir(parents=True, exist_ok=True)

    frame_numbers = parse_frames(args.frames)

    print("Загрузка YOLOX...")
    model, exp = load_yolox(str(weights_path))

    print("Сохранение выбранных кадров...")
    save_selected_frames(
        video_path=str(video_path),
        frame_numbers=frame_numbers,
        output_dir=output_dir,
        model=model,
        exp=exp,
    )

    print("Обработка всего видео...")
    process_video(
        video_path=str(video_path),
        output_video_path=output_dir / "result.mp4",
        model=model,
        exp=exp,
    )


if __name__ == "__main__":
    main()