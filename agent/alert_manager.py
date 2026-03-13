import logging
import pandas as pd
from typing import Dict, Any, List

try:
    from explainability.shap_explainer import ShapExplainer
    from explainability.threat_narrative import ThreatNarrativeGenerator
    from detection.attack_classifier import AttackClassifier
    from database import insert_anomaly
except ImportError:
    from agent.explainability.shap_explainer import ShapExplainer
    from agent.explainability.threat_narrative import ThreatNarrativeGenerator
    from agent.detection.attack_classifier import AttackClassifier
    from agent.database import insert_anomaly

logger = logging.getLogger(__name__)

class AlertManager:
    """
    Coordinates the process of taking raw anomaly predictions, generating
    explanations and narratives, and persisting them as alerts.
    """
    
    def __init__(self, ensemble_model, background_data: pd.DataFrame):
        self.ensemble_model = ensemble_model
        
        # Use first model in ensemble (Isolation Forest) for SHAP explainability
        # as TreeExplainer is much faster. Alternatively use KernelExplainer on ensemble.
        if hasattr(self.ensemble_model, 'models') and len(self.ensemble_model.models) > 0:
            self.shap_explainer = ShapExplainer(
                self.ensemble_model.models[0].model, 
                background_data, 
                is_tree_based=True
            )
        else:
            self.shap_explainer = ShapExplainer(self.ensemble_model, background_data)

    def process_predictions(self, df_features: pd.DataFrame, predictions: List[Dict[str, Any]]):
        """
        Process a batch of predictions, generate alerts for anomalies, and store them.
        
        Args:
            df_features: The dataframe containing the feature rows that were scored.
            predictions: The list of prediction dictionaries from the ensemble model.
        """
        if len(df_features) != len(predictions):
            logger.error("Mismatch between number of features and predictions.")
            return
            
        alerts_generated = 0
        
        for idx in range(len(predictions)):
            row = df_features.iloc[idx]
            pred = predictions[idx]
            
            # Only process actual anomalies
            if pred.get('is_anomaly', False):
                # 1. Classify the threat using heuristic rules
                threat_name, mitre_id = AttackClassifier.classify_anomaly(True, row.to_dict())
                
                # 2. Get top contributing features via SHAP for explainability
                # Exclude metadata columns
                feature_only_row = row[self.ensemble_model.models[0].features]
                top_features = self.shap_explainer.get_top_features(feature_only_row)
                
                # 3. Generate human-readable narrative
                narrative = ThreatNarrativeGenerator.generate_narrative(
                    True, threat_name, mitre_id, top_features, row.to_dict()
                )
                
                # 4. Store the alert
                anomaly_record = {
                    'log_id': int(row.get('id', 0)),
                    'model_name': pred.get('model_name', 'Unknown'),
                    'anomaly_score': pred.get('anomaly_score', 0.0),
                    'is_anomaly': True,
                    'threat_type': threat_name,
                    'mitre_technique': mitre_id,
                    'narrative': narrative
                }
                
                insert_anomaly(anomaly_record)
                alerts_generated += 1
                logger.info(f"Alert Generated: {threat_name} (Score: {pred['anomaly_score']:.2f}) - {narrative}")
                
        logger.info(f"Processed batch. Generated {alerts_generated} alerts.")
