from typing import Dict, Any, Tuple

try:
    from rule_engine import evaluate_rules
except ImportError:
    from agent.detection.rule_engine import evaluate_rules

class AttackClassifier:
    """
    Orchestrates the classification of anomalies flagged by ML models.
    Maps ML detections to specific threat intelligence frameworks (MITRE).
    """
    
    @staticmethod
    def classify_anomaly(is_anomaly: bool, feature_row: Dict[str, Any]) -> Tuple[str, str]:
        """
        Classifies the attack based on features if it was flagged as an anomaly.
        
        Args:
            is_anomaly: boolean output from ML ensemble.
            feature_row: feature dictionary for the event.
            
        Returns:
            Tuple of (Threat Name, MITRE Technique ID). 
            Returns ("None", "N/A") if not an anomaly.
        """
        if not is_anomaly:
            return "None", "N/A"
            
        # If the ML model says it's an anomaly, we use the rule engine to label it based on its features
        threat_name, mitre_id = evaluate_rules(feature_row)
        
        return threat_name, mitre_id
