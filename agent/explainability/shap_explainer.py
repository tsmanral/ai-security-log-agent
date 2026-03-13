import shap
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class ShapExplainer:
    """
    Generates explanations for model predictions using SHAP (SHapley Additive exPlanations).
    """
    
    def __init__(self, model, background_data: pd.DataFrame, is_tree_based: bool = False):
        """
        Initialize the explainer.
        
        Args:
            model: The trained ML model (must have a decision_function or predict method).
            background_data: A sample of historical (normal) data to use as the background distribution.
            is_tree_based: If True, uses TreeExplainer (optimized for IsolationForest).
        """
        self.model = model
        
        # We need a smaller background set if KernelExplainer is used due to performance
        if len(background_data) > 100 and not is_tree_based:
            self.background_data = shap.kmeans(background_data, 100)
        else:
            self.background_data = background_data
            
        self.is_tree_based = is_tree_based
        
        if self.is_tree_based:
            # For sklearn IsolationForest
            self.explainer = shap.TreeExplainer(model)
        else:
            # For models like OCSVM or Ensemble, use KernelExplainer with the score function
            # We want to explain the anomaly score
            def score_func(X):
                # Check if model is our custom wrapper or raw sklearn
                if hasattr(model, 'score_samples'):
                    return -model.score_samples(X)
                elif hasattr(model, 'predict'):
                    # Fallback for ensemble or raw predict
                    return model.predict(X) 
                
            self.explainer = shap.KernelExplainer(score_func, self.background_data)

    def explain_instance(self, instance: pd.Series) -> Dict[str, float]:
        """
        Explain a single anomaly prediction.
        
        Args:
            instance: A single row of feature data (pd.Series)
            
        Returns:
            Dict mapping feature names to their SHAP contribution values.
        """
        # Convert to single-row dataframe
        df_instance = pd.DataFrame([instance])
        
        try:
            shap_values = self.explainer.shap_values(df_instance)
            
            # Handle different shape outputs from different explainers
            if isinstance(shap_values, list):
                shap_values = shap_values[1] # Take positive class if classification
                
            if len(shap_values.shape) > 1:
                vals = shap_values[0]
            else:
                vals = shap_values
                
            # Create a dictionary of features and their SHAP contributions
            contributions = {feat: float(val) for feat, val in zip(df_instance.columns, vals)}
            
            # Sort by absolute contribution magnitude
            sorted_contributions = dict(sorted(contributions.items(), key=lambda item: abs(item[1]), reverse=True))
            return sorted_contributions
            
        except Exception as e:
            logger.error(f"Error generating SHAP values: {e}")
            return {}
            
    def get_top_features(self, instance: pd.Series, top_k: int = 3) -> List[str]:
        """Get the top K features that contributed most to the anomaly score."""
        contributions = self.explain_instance(instance)
        return list(contributions.keys())[:top_k]
