import pandas as pd
import numpy as np
from typing import Tuple, List, Dict


def load_severity_map(path: str) -> Dict[str, float]:
    try:
        df = pd.read_csv(path)
        df.columns = [c.strip() for c in df.columns]
        # Expect columns: Symptom, Weight
        if 'Symptom' in df.columns and 'Weight' in df.columns:
            return {row['Symptom'].strip().lower(): float(row['Weight']) for _, row in df.iterrows()}
    except Exception:
        pass
    return {}


def detect_symptom_columns(df: pd.DataFrame) -> List[str]:
    exclude = {'prognosis', 'disease', 'label'}
    cols = [c for c in df.columns if c.lower() not in exclude]
    # Filter out obvious duration columns
    symptom_cols = [c for c in cols if not (c.lower().startswith('duration_') or c.lower().endswith('_duration'))]
    return symptom_cols


def build_weighted_features(df: pd.DataFrame, severity_map: Dict[str, float]) -> Tuple[pd.DataFrame, List[str]]:
    # This function supports two dataset shapes:
    # 1) Binary indicator columns for each symptom (column name = symptom)
    # 2) Symptom list columns like Symptom_1..Symptom_N containing symptom names
    feature_cols = []
    features = pd.DataFrame(index=df.index)

    # detect list-style symptom columns (e.g., Symptom_1..Symptom_17)
    list_cols = [c for c in df.columns if c.lower().startswith('symptom')]
    if list_cols:
        # build set of unique symptoms
        uniq = set()
        for c in list_cols:
            uniq.update([str(x).strip() for x in df[c].dropna().unique() if str(x).strip()])
        uniq = sorted(uniq)
        for s in uniq:
            # presence if s appears in any Symptom_* column for that row
            presence = df[list_cols].apply(lambda row: int(s in [str(x).strip() for x in row if pd.notna(x)]), axis=1).astype(float)
            dur = pd.Series(np.ones(len(df)), index=df.index)
            sev = severity_map.get(s.strip().lower(), 1.0)
            weighted = presence * sev * dur
            colname = f'{s}__w'
            # sanitize column name (no commas)
            colname = colname.replace(' ', '_')
            features[colname] = weighted
            feature_cols.append(colname)
        return features, feature_cols

    # fallback: treat non-label columns as potential binary symptom columns
    symptom_cols = detect_symptom_columns(df)
    for s in symptom_cols:
        d_col1 = f'duration_{s}'
        d_col2 = f'{s}_duration'
        if d_col1 in df.columns:
            duration = df[d_col1].fillna(1).astype(float)
        elif d_col2 in df.columns:
            duration = df[d_col2].fillna(1).astype(float)
        else:
            duration = pd.Series(np.ones(len(df)), index=df.index)

        presence = df[s].fillna(0).astype(float)
        sev = severity_map.get(s.strip().lower(), 1.0)
        weighted = presence * sev * duration
        colname = f'{s}__w'
        features[colname] = weighted
        feature_cols.append(colname)

    return features, feature_cols


def load_dataset(path: str, severity_path: str = None) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
    df = pd.read_csv(path)
    severity_map = load_severity_map(severity_path) if severity_path else {}
    # detect label column case-insensitively
    label_candidates = {'prognosis', 'disease', 'label'}
    y_col = None
    for c in df.columns:
        if str(c).strip().lower() in label_candidates:
            y_col = c
            break
    if y_col is None:
        raise ValueError('No label column found. Expected one of prognosis/disease/label in dataset.')

    X, feature_names = build_weighted_features(df, severity_map)
    y = df[y_col].astype(str)
    return X, y, feature_names


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--dataset', default='dataset/dataset.csv')
    p.add_argument('--severity', default='dataset/Symptom-severity.csv')
    args = p.parse_args()
    X, y, features = load_dataset(args.dataset, args.severity)
    print('Built features:', features[:10])
    print('X shape', X.shape)
