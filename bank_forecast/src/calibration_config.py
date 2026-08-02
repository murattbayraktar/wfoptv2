"""Kalibrasyon config'i (`config/calibration.yaml`) için okuma/yazma yardımcıları.

`pipeline.load_config` ile birebir aynı desen izlenir: `yaml.safe_load`,
dosya yoksa boş sözlük, her çağrıda diskten taze okuma (cache yok) —
böylece dosya UI'dan güncellendiğinde süreç yeniden başlatılmadan devreye girer.
"""
import os
from datetime import datetime

import yaml

CALIBRATION_CONFIG_PATH = "config/calibration.yaml"


def default_calibration() -> dict:
    return {"multipliers": {}, "half_days": [], "updated_at": None}


def load_calibration(path: str = CALIBRATION_CONFIG_PATH) -> dict:
    data: dict = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

    defaults = default_calibration()
    return {
        "multipliers": data.get("multipliers") or defaults["multipliers"],
        "half_days": data.get("half_days") or defaults["half_days"],
        "updated_at": data.get("updated_at", defaults["updated_at"]),
    }


def save_calibration(data: dict, path: str = CALIBRATION_CONFIG_PATH) -> dict:
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    payload = {
        "multipliers": data.get("multipliers") or {},
        "half_days": sorted(set(data.get("half_days") or [])),
        "updated_at": datetime.now().isoformat(),
    }
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, allow_unicode=True, sort_keys=False)
    return payload
