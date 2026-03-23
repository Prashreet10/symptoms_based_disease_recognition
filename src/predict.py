import os
import json
import joblib
import pandas as pd
import numpy as np
import shap
try:
    from .preprocess import load_severity_map
except Exception:
    from preprocess import load_severity_map

# Get base directory (project root)
_base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def get_medical_tests_for_disease() -> dict:
    """Return a mapping of diseases to recommended medical tests for diagnosis."""
    disease_tests_map = {
        'drug reaction': ['Complete Blood Count (CBC)', 'Liver Function Tests (LFT)', 'Kidney Function Tests', 'Allergy Testing'],
        'malaria': ['Blood Smear Test', 'Rapid Diagnostic Test (RDT)', 'PCR Test', 'Complete Blood Count (CBC)'],
        'allergy': ['Skin Prick Test', 'Blood Test (IgE)', 'Patch Test', 'Allergy Panel'],
        'hypothyroidism': ['TSH Test', 'Free T4 Test', 'Free T3 Test', 'Thyroid Antibody Test'],
        'psoriasis': ['Skin Biopsy', 'Physical Examination', 'Blood Tests (to rule out other conditions)'],
        'gerd': ['Upper Endoscopy', 'Esophageal pH Monitoring', 'Barium Swallow Test', 'Esophageal Manometry'],
        'chronic cholestasis': ['Liver Function Tests (LFT)', 'Ultrasound', 'ERCP', 'Liver Biopsy'],
        'hepatitis a': ['Hepatitis A Antibody Test (Anti-HAV)', 'Liver Function Tests (LFT)', 'Complete Blood Count (CBC)'],
        'osteoarthristis': ['X-Ray', 'MRI', 'Blood Tests (to rule out other conditions)', 'Joint Fluid Analysis'],
        '(vertigo) paroymsal  positional vertigo': ['Dix-Hallpike Test', 'Videonystagmography (VNG)', 'MRI (to rule out other causes)'],
        'hypoglycemia': ['Blood Glucose Test', 'Fasting Blood Sugar', 'Oral Glucose Tolerance Test', 'C-Peptide Test'],
        'acne': ['Physical Examination', 'Hormone Tests (if severe)', 'Skin Culture (if infected)'],
        'diabetes ': ['Fasting Blood Sugar', 'HbA1c Test', 'Oral Glucose Tolerance Test', 'Random Blood Sugar'],
        'impetigo': ['Physical Examination', 'Bacterial Culture', 'Skin Swab Test'],
        'hypertension ': ['Blood Pressure Monitoring', 'Electrocardiogram (ECG)', 'Echocardiogram', 'Blood Tests'],
        'peptic ulcer diseae': ['Upper Endoscopy', 'H. Pylori Test', 'Barium Swallow', 'Biopsy'],
        'dimorphic hemmorhoids(piles)': ['Physical Examination', 'Digital Rectal Examination', 'Anoscopy', 'Colonoscopy (if needed)'],
        'common cold': ['Physical Examination', 'Rapid Antigen Test (to rule out flu)', 'Throat Swab (if needed)'],
        'chicken pox': ['Physical Examination', 'Blood Test (Varicella-Zoster Virus)', 'PCR Test'],
        'cervical spondylosis': ['X-Ray', 'MRI', 'CT Scan', 'Electromyography (EMG)'],
        'hyperthyroidism': ['TSH Test', 'Free T4 Test', 'Free T3 Test', 'Radioactive Iodine Uptake Test'],
        'urinary tract infection': ['Urinalysis', 'Urine Culture', 'Blood Tests', 'Imaging (if complicated)'],
        'varicose veins': ['Physical Examination', 'Duplex Ultrasound', 'Venography'],
        'aids': ['HIV Antibody Test', 'HIV RNA Test', 'CD4 Count', 'Viral Load Test'],
        'paralysis (brain hemorrhage)': ['CT Scan', 'MRI', 'Angiography', 'Lumbar Puncture'],
        'typhoid': ['Blood Culture', 'Widal Test', 'Typhidot Test', 'Stool Culture'],
        'hepatitis b': ['Hepatitis B Surface Antigen (HBsAg)', 'Hepatitis B Core Antibody', 'Liver Function Tests', 'HBV DNA Test'],
        'fungal infection': ['Skin Scraping', 'Fungal Culture', 'KOH Test', 'Wood Lamp Examination'],
        'hepatitis c': ['Hepatitis C Antibody Test', 'HCV RNA Test', 'Liver Function Tests', 'Liver Biopsy'],
        'migraine': ['Physical Examination', 'Neurological Exam', 'MRI (to rule out other causes)', 'CT Scan'],
        'bronchial asthma': ['Spirometry', 'Peak Flow Test', 'Chest X-Ray', 'Allergy Testing'],
        'alcoholic hepatitis': ['Liver Function Tests (LFT)', 'Complete Blood Count (CBC)', 'Ultrasound', 'Liver Biopsy'],
        'jaundice': ['Liver Function Tests (LFT)', 'Bilirubin Test', 'Complete Blood Count (CBC)', 'Ultrasound'],
        'hepatitis e': ['Hepatitis E Antibody Test', 'HEV RNA Test', 'Liver Function Tests'],
        'dengue': ['NS1 Antigen Test', 'Dengue IgM/IgG Test', 'Complete Blood Count (CBC)', 'PCR Test'],
        'hepatitis d': ['Hepatitis D Antibody Test', 'HDV RNA Test', 'Liver Function Tests'],
        'heart attack': ['Electrocardiogram (ECG)', 'Cardiac Enzyme Tests (Troponin)', 'Chest X-Ray', 'Echocardiogram'],
        'pneumonia': ['Chest X-Ray', 'Blood Tests', 'Sputum Culture', 'Pulse Oximetry'],
        'arthritis': ['Blood Tests (Rheumatoid Factor, ANA)', 'X-Ray', 'MRI', 'Joint Fluid Analysis'],
        'gastroenteritis': ['Stool Culture', 'Blood Tests', 'Physical Examination'],
        'tuberculosis': ['Tuberculin Skin Test', 'Chest X-Ray', 'Sputum Culture', 'IGRA Blood Test']
    }
    return disease_tests_map


def prepare_input(symptom_presence: dict, severity_map: dict, model_features: list) -> pd.DataFrame:
    # symptom_presence: {'fever': {'presence':1, 'duration':2}, ...} or {'fever':1}
    # Normalize symptom_presence keys to lowercase and handle spaces/underscores
    normalized_input = {}
    for key, value in symptom_presence.items():
        # Normalize: lowercase, replace spaces with underscores
        normalized_key = str(key).lower().strip().replace(' ', '_')
        normalized_input[normalized_key] = value
    
    rows = []
    feat = {}
    for mf in model_features:
        # mf like 'fever__w' or 'high_fever__w'
        s = mf.replace('__w', '')
        s_normalized = s.lower().strip()
        
        # Try exact match first, then try with spaces/underscores variations
        sp = normalized_input.get(s_normalized, None)
        if sp is None:
            # Try matching with space instead of underscore
            sp = normalized_input.get(s_normalized.replace('_', ' '), None)
        if sp is None:
            # Try matching with underscore instead of space
            for key in normalized_input.keys():
                if key.replace('_', ' ') == s_normalized.replace('_', ' '):
                    sp = normalized_input[key]
                    break
        
        if sp is None:
            pres = 0
            dur = 1
        elif isinstance(sp, dict):
            pres = float(sp.get('presence', 1))
            dur = float(sp.get('duration', 1))
        else:
            pres = float(sp)
            dur = 1
        sev = severity_map.get(s_normalized.replace('_', ' '), severity_map.get(s_normalized, 1.0))
        feat[mf] = pres * sev * dur
    return pd.DataFrame([feat])


def predict_from_input(sample_input: dict,
                       model_path=None,
                       encoder_path=None,
                       severity_path=None,
                       precaution_path=None) -> dict:
    """Return prediction dict for the provided sample_input."""
    # Resolve paths relative to project root
    if model_path is None:
        model_path = os.path.join(_base_dir, 'models', 'xgb_model.joblib')
    elif not os.path.isabs(model_path):
        model_path = os.path.join(_base_dir, model_path)
    
    if encoder_path is None:
        encoder_path = os.path.join(_base_dir, 'models', 'label_encoder.joblib')
    elif not os.path.isabs(encoder_path):
        encoder_path = os.path.join(_base_dir, encoder_path)
    
    if severity_path is None:
        severity_path = os.path.join(_base_dir, 'dataset', 'Symptom-severity.csv')
    elif not os.path.isabs(severity_path):
        severity_path = os.path.join(_base_dir, severity_path)
    
    if precaution_path is None:
        precaution_path = os.path.join(_base_dir, 'dataset', 'symptom_precaution.csv')
    elif not os.path.isabs(precaution_path):
        precaution_path = os.path.join(_base_dir, precaution_path)
    
    # Check if files exist
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    if not os.path.exists(encoder_path):
        raise FileNotFoundError(f"Encoder file not found: {encoder_path}")
    
    model = joblib.load(model_path)
    le = joblib.load(encoder_path)

    severity_map = load_severity_map(severity_path)
    # Get medical tests mapping instead of precautions
    medical_tests_map = get_medical_tests_for_disease()

    # feature names from model booster
    try:
        feature_names = list(model.get_booster().feature_names)
    except Exception:
        feature_names = list(getattr(model, 'feature_names_in_', []))

    X = prepare_input(sample_input, severity_map, feature_names)
    proba = model.predict_proba(X)[0]
    idx = int(np.argmax(proba))
    confidence = float(proba[idx])
    pred_label = le.inverse_transform([idx])[0]

    # Get input symptoms (normalized keys from sample_input)
    input_symptoms = [k.lower().strip().replace('_', ' ') for k in sample_input.keys()]
    
    # SHAP explanation for the single sample - get top contributing features
    shap_top = []
    top_symptoms = []
    try:
        explainer = shap.Explainer(model)
        sv = explainer(X)
        shap_vals = sv.values[0]
        
        # Create mapping of feature names to SHAP values
        feature_shap_map = dict(zip(feature_names, shap_vals))
        
        # Get top contributing features (by absolute SHAP value)
        top_features_by_shap = sorted(feature_shap_map.items(), key=lambda x: abs(x[1]), reverse=True)[:10]
        
        # Extract symptom names from top features (remove __w suffix and normalize)
        shap_top = []
        for feat_name, shap_val in top_features_by_shap:
            symptom_name = feat_name.replace('__w', '').replace('_', ' ').strip().title()
            # Only include if this symptom was in the input or has significant contribution
            if abs(shap_val) > 0.01:  # Threshold for significant contribution
                shap_top.append(symptom_name)
        
        # Also get top symptoms from input based on their SHAP values
        input_feature_shap = {}
        for symptom in input_symptoms:
            # Try to find matching feature
            symptom_normalized = symptom.replace(' ', '_')
            for feat_name in feature_names:
                if feat_name.replace('__w', '').lower() == symptom_normalized.lower():
                    input_feature_shap[symptom] = abs(feature_shap_map.get(feat_name, 0))
                    break
        
        # Sort input symptoms by their SHAP contribution
        top_symptoms = sorted(input_feature_shap.items(), key=lambda x: x[1], reverse=True)[:5]
        top_symptoms = [s[0].title() for s in top_symptoms]  # Capitalize for display
        
        # If no input-based symptoms, use top SHAP features
        if not top_symptoms:
            top_symptoms = shap_top[:5]
            
    except Exception as e:
        # Fallback to feature importance if SHAP fails
        try:
            fi = getattr(model, 'feature_importances_', None)
            if fi is not None:
                fi_map = dict(zip(feature_names, fi))
                # Filter to only input symptoms
                input_feature_importance = {}
                for symptom in input_symptoms:
                    symptom_normalized = symptom.replace(' ', '_')
                    for feat_name, importance in fi_map.items():
                        if feat_name.replace('__w', '').lower() == symptom_normalized.lower():
                            input_feature_importance[symptom] = importance
                            break
                
                top_symptoms = sorted(input_feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
                top_symptoms = [s[0].title() for s in top_symptoms]  # Capitalize for display
        except Exception:
            # Last resort: use input symptoms as-is
            top_symptoms = [s.title() for s in input_symptoms[:5]]  # Capitalize for display
        print(f"SHAP explanation failed: {e}")

    recommended = recommend_tests(top_symptoms or shap_top[:5], confidence, medical_tests_map, pred_label)

    # Ensure we have at least some symptoms to display
    if not top_symptoms and shap_top:
        top_symptoms = shap_top[:5]
    elif not top_symptoms and input_symptoms:
        top_symptoms = [s.title() for s in input_symptoms[:5]]
    
    # Ensure we have SHAP results
    if not shap_top and top_symptoms:
        shap_top = top_symptoms
    
    result = {
        'prediction': pred_label,
        'confidence': confidence,
        'top_features_by_model': top_symptoms[:5],  # Limit to 5
        'top_features_by_shap': shap_top[:5],  # Limit to 5
        'recommended_tests': recommended,
    }
    return result


def recommend_tests(top_symptoms: list, confidence: float, medical_tests_map: dict, predicted_disease: str = None) -> list:
    """Recommend medical tests to confirm the predicted disease."""
    tests = []
    
    # Primary: Get tests based on predicted disease
    if predicted_disease:
        disease_normalized = str(predicted_disease).strip().lower()
        # Try exact match first
        disease_tests = medical_tests_map.get(disease_normalized, [])
        if disease_tests:
            tests.extend(disease_tests)
        
        # If no exact match, try fuzzy matching for disease name variations
        if not tests:
            # Try matching with common variations (remove extra spaces, parentheses content)
            disease_clean = disease_normalized.replace('(', '').replace(')', '').strip()
            for disease_key in medical_tests_map.keys():
                key_clean = disease_key.replace('(', '').replace(')', '').strip()
                # Exact match after cleaning
                if disease_clean == key_clean:
                    tests.extend(medical_tests_map[disease_key])
                    break
                # Check if predicted disease contains key words from known diseases
                disease_words = set(disease_clean.split())
                key_words = set(key_clean.split())
                # If there's significant overlap (at least 2 words match), use those tests
                if len(disease_words.intersection(key_words)) >= min(2, len(key_words)):
                    tests.extend(medical_tests_map[disease_key])
                    break
    
    # Remove duplicates while preserving order
    seen = set()
    unique_tests = []
    for test in tests:
        test_lower = test.lower()
        if test_lower not in seen:
            seen.add(test_lower)
            unique_tests.append(test)
    
    # If still no tests, add general diagnostic tests based on symptoms
    if not unique_tests:
        # Add common tests based on symptom categories
        if any('fever' in s.lower() or 'chills' in s.lower() for s in top_symptoms):
            unique_tests.append('Complete Blood Count (CBC)')
            unique_tests.append('Blood Culture')
        if any('pain' in s.lower() or 'ache' in s.lower() for s in top_symptoms):
            unique_tests.append('Physical Examination')
            unique_tests.append('Blood Tests')
        if any('skin' in s.lower() or 'rash' in s.lower() for s in top_symptoms):
            unique_tests.append('Skin Examination')
            unique_tests.append('Skin Biopsy (if needed)')
    
    # confidence thresholds - adjust number of tests based on confidence
    if confidence >= 0.85:
        # High confidence - show essential diagnostic tests
        return unique_tests[:6]
    elif confidence >= 0.5:
        # Medium confidence - show more comprehensive tests
        return unique_tests[:8]
    else:
        # Low confidence - show broader diagnostic panel
        return unique_tests[:10]


if __name__ == '__main__':
    # simple CLI example
    example = {
        'fever': {'presence': 1, 'duration': 3},
        'cough': {'presence': 1, 'duration': 2},
    }
    print(json.dumps(predict_from_input(example), indent=2))
