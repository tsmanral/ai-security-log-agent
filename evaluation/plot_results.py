import pandas as pd
import matplotlib.pyplot as plt
import os

def render_feature_importance_plot(shap_dict: dict, output_path: str):
    """
    Renders a simple horizontal bar chart of SHAP feature importances.
    
    Args:
        shap_dict: Dictionary mapping feature strings to float importance scores.
        output_path: Path to save the PNG image.
    """
    if not shap_dict:
        return
        
    # Sort absolute values
    sorted_items = sorted(shap_dict.items(), key=lambda x: abs(x[1]))
    features = [item[0] for item in sorted_items]
    importances = [abs(item[1]) for item in sorted_items]
    
    plt.figure(figsize=(10, 6))
    plt.barh(features, importances, color='skyblue')
    plt.xlabel('Absolute SHAP Value (Impact on Anomaly Score)')
    plt.title('Top Feature Importances for Detected Anomaly')
    plt.tight_layout()
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    plt.close()
