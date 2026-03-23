import pandas as pd
import os


def get_dataset_path(base_dir=None):
    if base_dir is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    return os.path.join(base_dir, 'dataset', 'dataset.csv')


def get_severity_path(base_dir=None):
    if base_dir is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    return os.path.join(base_dir, 'dataset', 'Symptom-severity.csv')


def get_all_dataset_diseases(dataset_path=None):
    """Return list of {name, symptom_count} sorted by name."""
    if dataset_path is None:
        dataset_path = get_dataset_path()
    try:
        df = pd.read_csv(dataset_path)
        # Find label column
        label_col = None
        for c in df.columns:
            if c.strip().lower() in ('disease', 'prognosis', 'label'):
                label_col = c
                break
        if label_col is None:
            return []
        symptom_cols = [c for c in df.columns if c.lower().startswith('symptom')]
        result = []
        for disease_name, group in df.groupby(label_col):
            # count unique non-null symptoms across all rows for this disease
            syms = set()
            for c in symptom_cols:
                vals = group[c].dropna().astype(str).str.strip()
                syms.update([v for v in vals if v and v.lower() != 'nan'])
            result.append({
                'name': str(disease_name).strip(),
                'symptom_count': len(syms),
                'row_count': len(group),
            })
        result.sort(key=lambda x: x['name'].lower())
        return result
    except Exception as e:
        print(f"Error reading dataset diseases: {e}")
        return []


def get_dataset_stats(dataset_path=None, severity_path=None):
    """Return {disease_count, symptom_count, total_rows}."""
    if dataset_path is None:
        dataset_path = get_dataset_path()
    if severity_path is None:
        severity_path = get_severity_path()
    try:
        df = pd.read_csv(dataset_path)
        label_col = None
        for c in df.columns:
            if c.strip().lower() in ('disease', 'prognosis', 'label'):
                label_col = c
                break
        disease_count = df[label_col].nunique() if label_col else 0

        symptom_cols = [c for c in df.columns if c.lower().startswith('symptom')]
        all_syms = set()
        for c in symptom_cols:
            vals = df[c].dropna().astype(str).str.strip()
            all_syms.update([v for v in vals if v and v.lower() != 'nan'])
        symptom_count = len(all_syms)

        return {
            'disease_count': int(disease_count),
            'symptom_count': int(symptom_count),
            'total_rows': int(len(df)),
        }
    except Exception as e:
        print(f"Error getting stats: {e}")
        return {'disease_count': 0, 'symptom_count': 0, 'total_rows': 0}


def add_disease_to_dataset(disease_name, description, symptoms_str, dataset_path=None):
    """
    Add rows to the dataset CSV for the given disease and its symptoms.
    symptoms_str: comma-separated symptom names.
    Adds one row with all symptoms spread across Symptom_1..Symptom_N columns.
    """
    if dataset_path is None:
        dataset_path = get_dataset_path()
    try:
        df = pd.read_csv(dataset_path)
        # Find label column
        label_col = None
        for c in df.columns:
            if c.strip().lower() in ('disease', 'prognosis', 'label'):
                label_col = c
                break
        if label_col is None:
            raise ValueError('No label column found in dataset')

        symptoms_list = [s.strip() for s in symptoms_str.split(',') if s.strip()]
        symptom_cols = [c for c in df.columns if c.lower().startswith('symptom')]

        new_row = {col: '' for col in df.columns}
        new_row[label_col] = disease_name.strip()

        for i, symptom in enumerate(symptoms_list):
            if i < len(symptom_cols):
                new_row[symptom_cols[i]] = symptom

        if 'Description' in new_row:
            new_row['Description'] = description or ''

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(dataset_path, index=False)
        return True, None
    except Exception as e:
        print(f"Error adding disease to dataset: {e}")
        return False, str(e)


def delete_disease_from_dataset(disease_name, dataset_path=None):
    """Remove all rows for the given disease from dataset CSV."""
    if dataset_path is None:
        dataset_path = get_dataset_path()
    try:
        df = pd.read_csv(dataset_path)
        label_col = None
        for c in df.columns:
            if c.strip().lower() in ('disease', 'prognosis', 'label'):
                label_col = c
                break
        if label_col is None:
            return False, 'No label column found'
        original_len = len(df)
        df = df[df[label_col].astype(str).str.strip() != disease_name.strip()]
        removed = original_len - len(df)
        df.to_csv(dataset_path, index=False)
        return True, f'Removed {removed} rows for {disease_name}'
    except Exception as e:
        print(f"Error deleting disease: {e}")
        return False, str(e)


def get_all_symptoms(dataset_path=None, severity_path=None):
    """Return sorted list of all unique symptom names from dataset."""
    if dataset_path is None:
        dataset_path = get_dataset_path()
    if severity_path is None:
        severity_path = get_severity_path()
    symptoms = set()
    try:
        if os.path.exists(dataset_path):
            df = pd.read_csv(dataset_path)
            symptom_cols = [c for c in df.columns if c.lower().startswith('symptom')]
            for c in symptom_cols:
                vals = df[c].dropna().astype(str).str.strip()
                symptoms.update([v for v in vals if v and v.lower() != 'nan'])
    except Exception:
        pass
    try:
        if os.path.exists(severity_path):
            sdf = pd.read_csv(severity_path)
            if 'Symptom' in sdf.columns:
                symptoms.update([str(v).strip() for v in sdf['Symptom'].dropna() if str(v).strip()])
    except Exception:
        pass
    return sorted(symptoms)
