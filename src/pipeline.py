import argparse
import json
from pathlib import Path
import cv2
import numpy as np
from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator, colors

from .identifier import PlayerIdentifier
from .utils import draw_box_with_label

def run(args):
    out_dir = Path('outputs')
    out_dir.mkdir(exist_ok=True, parents=True)

    # Load model
    model = YOLO(args.yolo_weights)  # e.g., yolov8x.pt or fine-tuned weights
    tracker_cfg = args.tracker or str(Path(__file__).resolve().parents[1] / 'configs' / 'bytetrack.yaml')

    # Video IO
    cap = cv2.VideoCapture(str(args.source))
    assert cap.isOpened(), f"Cannot open source: {args.source}"
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(str(out_dir / 'annotated.mp4'), fourcc, fps, (width, height))

    identifier = PlayerIdentifier(device=args.device)

    all_frames = []
    frame_idx = 0

    # Use Ultralytics built-in tracker generator
    results = model.track(source=str(args.source),
                          stream=True,
                          conf=args.conf,
                          iou=args.iou,
                          device=args.device,
                          tracker=tracker_cfg,
                          persist=True,
                          verbose=False)

    for res in results:
        # res is a 'Results' object for current frame
        frame = res.orig_img.copy()
        frame_tracks = []

        if res.boxes is not None and res.boxes.id is not None:
            ids = res.boxes.id.cpu().numpy().astype(int)
            xyxy = res.boxes.xyxy.cpu().numpy()
            cls = res.boxes.cls.cpu().numpy().astype(int)
            conf = res.boxes.conf.cpu().numpy()

            for tid, box, c, cf in zip(ids, xyxy, cls, conf):
                # Update identifier with jersey OCR + appearance emb
                identifier.update(frame, int(tid), box)
                ident = identifier.get_identity(int(tid))
                label = f"ID {int(tid)}"
                if ident['jersey']['value']:
                    label += f" | #{ident['jersey']['value']}"
                label += f" | {cf:.2f}"
                draw_box_with_label(frame, box, label, color=colors(c, True))

                frame_tracks.append({
                    'track_id': int(tid),
                    'bbox_xyxy': [float(x) for x in box.tolist()],
                    'cls': int(c),
                    'conf': float(cf),
                    'jersey': ident['jersey']
                })

        writer.write(frame)
        all_frames.append({
            'frame_index': frame_idx,
            'tracks': frame_tracks
        })
        frame_idx += 1

    writer.release()
    cap.release()

    # Save per-frame tracks
    with open(out_dir / 'tracks.json', 'w') as f:
        json.dump(all_frames, f)

    # Save per-player consolidated identities
    players = {}
    for tid in identifier.track_id_counts.keys():
        players[int(tid)] = identifier.get_identity(int(tid))
    with open(out_dir / 'players.json', 'w') as f:
        json.dump(players, f)

    print("Saved:", out_dir / 'annotated.mp4', out_dir / 'tracks.json', out_dir / 'players.json')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Player detection, tracking, identification')
    parser.add_argument('--source', type=str, required=True, help='Path to video file or stream URL')
    parser.add_argument('--yolo-weights', type=str, default='yolov8x.pt', help='YOLOv8 weights')
    parser.add_argument('--device', type=str, default='cpu', help='cpu or cuda:0')
    parser.add_argument('--conf', type=float, default=0.25)
    parser.add_argument('--iou', type=float, default=0.45)
    parser.add_argument('--tracker', type=str, default=None, help='Path to tracker yaml (ByteTrack)')
    args = parser.parse_args()
    run(args)
