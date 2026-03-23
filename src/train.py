import os
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb
try:
    from .preprocess import load_dataset
except Exception:
    from preprocess import load_dataset
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, confusion_matrix
import json


def train(dataset_path='dataset/dataset.csv', severity_path='dataset/Symptom-severity.csv', out_dir='models'):
    os.makedirs(out_dir, exist_ok=True)
    X, y, feature_names = load_dataset(dataset_path, severity_path)

    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    # Stratified split requires at least 2 samples in every class.
    # When the admin adds a new disease, it may initially have only 1 row in the dataset,
    # which would make stratification fail. Fall back to a non-stratified split in that case.
    class_counts = pd.Series(y_enc).value_counts()
    stratify = y_enc if class_counts.min() >= 2 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y_enc,
        test_size=0.2,
        random_state=42,
        stratify=stratify,
    )

    # Suppress verbose training output (important when running via subprocess).
    model = xgb.XGBClassifier(
        use_label_encoder=False,
        eval_metric='mlogloss',
        n_jobs=-1,
        verbosity=0,
    )
    model.fit(X_train, y_train, verbose=False)

    joblib.dump(model, os.path.join(out_dir, 'xgb_model.joblib'))
    joblib.dump(le, os.path.join(out_dir, 'label_encoder.joblib'))

    # Evaluate on test set
    y_pred = model.predict(X_test)
    y_proba = None
    try:
        y_proba = model.predict_proba(X_test)
    except Exception:
        y_proba = None

    metrics = {}
    metrics['accuracy'] = float(accuracy_score(y_test, y_pred))
    # for multi-class, average='weighted' gives per-class weighted metric
    metrics['precision'] = float(precision_score(y_test, y_pred, average='weighted', zero_division=0))
    metrics['recall'] = float(recall_score(y_test, y_pred, average='weighted', zero_division=0))
    metrics['f1'] = float(f1_score(y_test, y_pred, average='weighted', zero_division=0))
    metrics['confusion_matrix'] = confusion_matrix(y_test, y_pred).tolist()

    # save classification report
    metrics['classification_report'] = classification_report(y_test, y_pred, zero_division=0, output_dict=True)

    with open(os.path.join(out_dir, 'metrics.json'), 'w', encoding='utf-8') as fh:
        json.dump(metrics, fh, indent=2)

    print('Evaluation metrics saved to', os.path.join(out_dir, 'metrics.json'))

    # feature importances
    fi = getattr(model, 'feature_importances_', None)
    if fi is not None:
        fi_df = pd.DataFrame({'feature': X.columns, 'importance': fi})
        fi_df = fi_df.sort_values('importance', ascending=False)
        fi_df.to_csv(os.path.join(out_dir, 'feature_importances.csv'), index=False)

    print('Training complete. Model and artifacts saved to', out_dir)


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--dataset', default='dataset/dataset.csv')
    p.add_argument('--severity', default='dataset/Symptom-severity.csv')
    p.add_argument('--out', default='models')
    args = p.parse_args()
    train(args.dataset, args.severity, args.out)
