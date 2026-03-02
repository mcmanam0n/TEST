import pandas as pd

FEATURE_COLUMNS = [
    'offstr_diff', 'defstr_diff', 'oe_roll_diff', 'de_roll_diff',
    'tempo_A', 'tempo_B', 'expected_tempo', 'efg_A_vs_B', 'efg_B_vs_A',
    'to_A_vs_B', 'to_B_vs_A', 'orb_A_vs_B', 'orb_B_vs_A',
    'ftr_A_vs_B', 'ftr_B_vs_A', 'neutral', 'games_played_A', 'games_played_B'
]


def build_matchup_features(teamA: pd.Series, teamB: pd.Series, neutral: int) -> dict:
    return {
        'offstr_diff': teamA['OffStr'] - teamB['OffStr'],
        'defstr_diff': teamB['DefStr'] - teamA['DefStr'],
        'oe_roll_diff': teamA['OE'] - teamB['OE'],
        'de_roll_diff': teamB['DE'] - teamA['DE'],
        'tempo_A': teamA['tempo'],
        'tempo_B': teamB['tempo'],
        'expected_tempo': 0.5 * (teamA['tempo'] + teamB['tempo']),
        'efg_A_vs_B': teamA['eFG_off'] - teamB['eFG_def'],
        'efg_B_vs_A': teamB['eFG_off'] - teamA['eFG_def'],
        'to_A_vs_B': teamA['TO_off'] - teamB['TO_def'],
        'to_B_vs_A': teamB['TO_off'] - teamA['TO_def'],
        'orb_A_vs_B': teamA['ORB_off'] - teamB['DRB_def'],
        'orb_B_vs_A': teamB['ORB_off'] - teamA['DRB_def'],
        'ftr_A_vs_B': teamA['FTR_off'] - teamB['FTR_def'],
        'ftr_B_vs_A': teamB['FTR_off'] - teamA['FTR_def'],
        'neutral': neutral,
        'games_played_A': teamA['games_played'],
        'games_played_B': teamB['games_played'],
    }
