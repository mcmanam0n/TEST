from pathlib import Path
import subprocess


def test_smoke_pipeline():
    root = Path(__file__).resolve().parents[1]
    cmd = ['python', 'scripts/run_pretrain_asof.py', '--asof', '2026-03-01']
    subprocess.check_call(cmd, cwd=root)
    assert (root / 'artifacts/checkpoints/2026-03-01/win_model.pkl').exists()
    cmd2 = ['python', 'scripts/run_game.py', '--asof', '2026-03-01', '--teamA', 'Duke', '--teamB', 'Kansas', '--neutral', '1', '--sims', '500']
    subprocess.check_call(cmd2, cwd=root)
    assert (root / 'outputs/game_Duke_vs_Kansas_2026-03-01.json').exists()
