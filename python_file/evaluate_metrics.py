from sklearn.metrics import precision_score, accuracy_score, recall_score, f1_score, confusion_matrix
import pandas as pd
import re
import seaborn as sns
import matplotlib.pyplot as plt

def evaluate_matching_algorithm(df,truth_col, pred_col):
  
    extract_digits = lambda x: "".join(re.findall(r'\d+', str(x))) if (not pd.isnull(x) and re.findall(r'\d+', str(x))) else "Missing"

    # Transformation des colonnes en appliquant l'extraction des chiffres
    y_true = df[truth_col].apply(extract_digits)
    y_pred = df[pred_col].apply(extract_digits)


    y_true_binary = y_true == y_pred
    y_pred_binary = y_pred.notnull()
    
    # Calcul des métriques sur les valeurs transformées
    accuracy = accuracy_score(y_true, y_pred)
    recall = recall_score(y_true_binary, y_pred_binary, zero_division=0)
    precision = precision_score(y_true_binary, y_pred_binary, zero_division=0)
    f1 = f1_score(y_true_binary, y_pred_binary, zero_division=0)
    
    metrics = {
        'precision': precision,
        'accuracy': accuracy,
        'recall': recall,
        'f1': f1
    }
    print("=== Évaluation du Matching ===")
    print(f"Accuracy  : {accuracy:.2f}")
    print(f"Recall    : {recall:.2f}")
    print(f"Precision : {precision:.2f}")
    print(f"F1-score  : {f1:.2f}")
    print("\nMatrice de confusion :")
    # Création de la matrice de confusion
    #conf_matrix = confusion_matrix(y_true, y_pred)
    
    conf_matrix = confusion_matrix(y_true_binary, y_pred_binary)
    
    # Visualisation
    plt.figure(figsize=(8, 6))
    sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['Mismatch', 'Match'], 
                yticklabels=['Mismatch', 'Match'])
    plt.xlabel('Prédit')
    plt.ylabel('Réel')
    plt.title('Matrice de Confusion')
    
    return metrics, conf_matrix
