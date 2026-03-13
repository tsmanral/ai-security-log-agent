import pandas as pd
import numpy as np
from typing import Dict, Any, List

try:
    from base_model import BaseAnomalyDetector
    from isolation_forest import IFDetector
    from local_outlier_factor import LOFDetector
    from one_class_svm import OCSVMDetector
except ImportError:
    from agent.models.base_model import BaseAnomalyDetector
    from agent.models.isolation_forest import IFDetector
    from agent.models.local_outlier_factor import LOFDetector
    from agent.models.one_class_svm import OCSVMDetector

class EnsembleDetector:
    """
    Ensemble anomaly detector that combines predictions from multiple base models
    using a voting mechanism or score averaging.
    """
    
    def __init__(self):
        # Initialize base models
        self.models: List[BaseAnomalyDetector] = [
            IFDetector(contamination=0.05),
            LOFDetector(contamination=0.05, n_neighbors=25),
            OCSVMDetector(nu=0.05)
        ]

    def train(self, df: pd.DataFrame):
        """
        Train all underlying models on the feature data.
        
        Args:
            df (pd.DataFrame): Training feature data.
        """
        for model in self.models:
            model.train(df)

    def predict(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Predict anomalies using an ensemble approach (Majority Vote).
        
        Args:
            df (pd.DataFrame): Data to predict on.
            
        Returns:
            List[Dict[str, Any]]: Ensemble prediction results for each row.
        """
        if df.empty:
            return []
            
        all_preds = []
        for model in self.models:
            all_preds.append(model.predict(df))
            
        # all_preds is a List of Model Predictions
        # e.g., all_preds[0] is IF predictions, all_preds[1] is LOF
        
        n_samples = len(df)
        n_models = len(self.models)
        
        ensemble_results = []
        
        for i in range(n_samples):
            votes = 0
            scores = []
            model_details = []
            
            for m_idx in range(n_models):
                pred = all_preds[m_idx][i]
                if pred['is_anomaly']:
                    votes += 1
                scores.append(pred['anomaly_score'])
                
                model_details.append({
                    'model': self.models[m_idx].name,
                    'is_anomaly': pred['is_anomaly'],
                    'score': pred['anomaly_score']
                })
                
            # Ensemble decision: Majority rules (>= 2 out of 3 models flag as anomaly)
            is_anomaly = votes >= (n_models / 2)
            avg_score = np.mean(scores)
            
            ensemble_results.append({
                'is_anomaly': is_anomaly,
                'anomaly_score': float(avg_score), # Average raw score for ranking
                'votes': votes,
                'total_models': n_models,
                'details': model_details,
                'model_name': "Ensemble_Voting"
            })
            
        return ensemble_results
