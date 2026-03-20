import torch
import torch.nn as nn
import torchvision.models as models
import torch.nn.functional as F
import numpy as np
import cv2

from .ocr import JerseyOCR

OCR_CROP_RATIO = (0.15, 0.65)  # take upper 65% height, center 70% width heuristically

class AppearanceEmbedder(nn.Module):
    def __init__(self, device='cpu'):
        super().__init__()
        base = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
        self.feature_extractor = nn.Sequential(*(list(base.children())[:-1]))  # Bx512x1x1
        self.device = device
        self.eval().to(device)

    @torch.no_grad()
    def embed(self, img_bgr):
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img_rgb, (224, 224))
        img = torch.from_numpy(img).float().permute(2,0,1) / 255.0
        # normalize
        mean = torch.tensor([0.485, 0.456, 0.406]).view(3,1,1)
        std = torch.tensor([0.229, 0.224, 0.225]).view(3,1,1)
        img = (img - mean) / std
        img = img.unsqueeze(0).to(self.device)
        feat = self.feature_extractor(img).view(1, -1)  # 512-d
        feat = F.normalize(feat, dim=1)  # unit norm
        return feat.squeeze(0).cpu().numpy()

class PlayerIdentifier:
    def __init__(self, device='cpu'):
        self.ocr = JerseyOCR()
        self.embedder = AppearanceEmbedder(device=device)
        self.track_id_to_jersey = {}   # track_id -> {'value': str, 'conf': float}
        self.track_id_to_embed = {}    # track_id -> np.array (running mean)
        self.track_id_counts = {}      # for running mean

    def _crop_jersey_region(self, frame, box):
        x1, y1, x2, y2 = map(int, box)
        w = max(1, x2 - x1)
        h = max(1, y2 - y1)
        rx = int(w * 0.15)
        rw = int(w * 0.70)
        ry = int(h * 0.05)
        rh = int(h * 0.65)
        cx1 = x1 + rx
        cy1 = y1 + ry
        cx2 = min(x1 + rx + rw, frame.shape[1])
        cy2 = min(y1 + ry + rh, frame.shape[0])
        crop = frame[cy1:cy2, cx1:cx2].copy()
        return crop

    def update(self, frame, track_id, box):
        # Jersey OCR (digits only)
        crop = self._crop_jersey_region(frame, box)
        jersey, conf = self.ocr.read_digits(crop)
        if jersey:
            prev = self.track_id_to_jersey.get(track_id, {'value': None, 'conf': 0.0})
            # keep the higher confidence or consistent reading
            if conf >= prev['conf'] or prev['value'] is None or prev['value'] == jersey:
                self.track_id_to_jersey[track_id] = {'value': jersey, 'conf': float(conf)}
        # Appearance embedding running mean
        emb = self.embedder.embed(crop if crop.size else frame)
        if track_id not in self.track_id_counts:
            self.track_id_counts[track_id] = 0
            self.track_id_to_embed[track_id] = emb
        else:
            n = self.track_id_counts[track_id]
            self.track_id_to_embed[track_id] = (self.track_id_to_embed[track_id]*n + emb) / (n+1)
        self.track_id_counts[track_id] += 1

    def get_identity(self, track_id):
        jersey_info = self.track_id_to_jersey.get(track_id, {'value': None, 'conf': 0.0})
        emb = self.track_id_to_embed.get(track_id, None)
        return {'jersey': jersey_info, 'embedding': emb.tolist() if emb is not None else None}
