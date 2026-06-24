import argparse
from pathlib import Path

import av
import cv2
import torch

from yolox.data.data_augment import preproc
from yolox.exp import get_exp
from yolox.utils import postprocess


OUTPUT_DIR = Path("results")
WEIGHTS_PATH = "weights/yolox_s.pth"
OUTPUT_VIDEO = OUTPUT_DIR / "output_circles.mp4"


def parse_frames(frames_text):
    return [int(x) for x in frames_text.split(",")]


def frame_to_bgr(frame):
    image_rgb = frame.to_ndarray(format="rgb24")
    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    return image_bgr


def load_yolox():
    exp = get_exp(None, "yolox-s")
    exp.test_size = (640, 640)
    exp.test_conf = 0.25
    exp.nmsthre = 0.45

    model = exp.get_model()
    model.eval()

    checkpoint = torch.load(WEIGHTS_PATH, map_location="cpu", weights_only=False)
    model.load_state_dict(checkpoint["model"])

    return model, exp


def detect_objects(model, exp, image_bgr):
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

    height, width = image_bgr.shape[:2]

    result = []
    detections = output[0].cpu().numpy()
    boxes = detections[:, 0:4] / ratio

    for box in boxes:
        x1, y1, x2, y2 = box.astype(int)

        x1 = max(0, min(x1, width - 1))
        y1 = max(0, min(y1, height - 1))
        x2 = max(0, min(x2, width - 1))
        y2 = max(0, min(y2, height - 1))

        result.append((x1, y1, x2, y2))

    return result


def draw_rectangles(image_bgr, boxes):
    result = image_bgr.copy()

    for x1, y1, x2, y2 in boxes:
        cv2.rectangle(result, (x1, y1), (x2, y2), (0, 255, 0), 2)

    return result


def draw_circles(image_bgr, boxes):
    result = image_bgr.copy()

    for x1, y1, x2, y2 in boxes:
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        radius = max(x2 - x1, y2 - y1) // 2

        cv2.circle(result, (center_x, center_y), radius, (0, 0, 255), 2)

    return result


def process_selected_frames(video_path, frame_numbers, model, exp):
    needed_frames = set(frame_numbers)

    with av.open(video_path) as container:
        stream = container.streams.video[0]

        for frame_number, frame in enumerate(container.decode(stream), start=1):
            if frame_number in needed_frames:
                image_bgr = frame_to_bgr(frame)

                cv2.imwrite(
                    str(OUTPUT_DIR / f"frame_{frame_number}.jpg"),
                    image_bgr,
                )

                boxes = detect_objects(model, exp, image_bgr)

                image_with_rectangles = draw_rectangles(image_bgr, boxes)
                image_with_circles = draw_circles(image_bgr, boxes)

                cv2.imwrite(
                    str(OUTPUT_DIR / f"frame_{frame_number}_rect.jpg"),
                    image_with_rectangles,
                )

                cv2.imwrite(
                    str(OUTPUT_DIR / f"frame_{frame_number}_circle.jpg"),
                    image_with_circles,
                )

                print(f"Сохранён кадр {frame_number}")

            if frame_number > max(frame_numbers):
                break


def get_fps(stream):
    if stream.average_rate is not None:
        return float(stream.average_rate)

    return 25.0


def process_video(video_path, model, exp):
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
                    str(OUTPUT_VIDEO),
                    fourcc,
                    fps,
                    (width, height),
                )

            writer.write(result)

            if frame_number % 30 == 0:
                print(f"Обработано кадров: {frame_number}")

        writer.release()

    print(f"Видео сохранено: {OUTPUT_VIDEO}")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Путь к видеофайлу",
    )

    parser.add_argument(
        "--frames",
        default="100,200,234",
        help="Номера кадров через запятую",
    )

    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)

    frame_numbers = parse_frames(args.frames)

    model, exp = load_yolox()

    process_selected_frames(args.input, frame_numbers, model, exp)
    process_video(args.input, model, exp)


if __name__ == "__main__":
    main()

