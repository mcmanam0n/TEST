from pathlib import Path
import joblib
from ncaam_sim.utils.io import ensure_dir, write_json


def save_artifacts(base_dir: Path, win_model, margin_model, calibrator, scaler, config: dict, metrics: dict) -> None:
    ensure_dir(base_dir)
    joblib.dump(win_model, base_dir / 'win_model.pkl')
    joblib.dump(margin_model, base_dir / 'margin_model.pkl')
    joblib.dump(calibrator, base_dir / 'calibrator.pkl')
    joblib.dump(scaler, base_dir / 'scaler.pkl')
    write_json(base_dir / 'config.json', config)
    write_json(base_dir / 'metrics.json', metrics)
