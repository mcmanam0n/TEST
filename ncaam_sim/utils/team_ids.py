from pathlib import Path
import pandas as pd


DEFAULT_ALIASES = {
    'Univ. of Kansas': 'Kansas',
    'Duke Blue Devils': 'Duke',
}


def canonicalize_team(name: str, aliases: dict[str, str] | None = None) -> str:
    aliases = aliases or DEFAULT_ALIASES
    return aliases.get(name, name).strip()


def load_alias_overrides(path: Path = Path('data/team_aliases.csv')) -> dict[str, str]:
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    return dict(zip(df['alias'], df['canonical']))
