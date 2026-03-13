from typing import Dict, Any, Tuple

def evaluate_rules(feature_row: Dict[str, Any]) -> Tuple[str, str]:
    """
    Evaluate heuristics and rule-based thresholds to classify an attack.
    
    Args:
        feature_row: Dictionary containing behavioral and temporal features.
        
    Returns:
        Tuple of (Threat Name, MITRE ATT&CK ID)
    """
    failures = feature_row.get('failures_15m', 0)
    users = feature_row.get('unique_users_15m', 0)
    success = feature_row.get('successes_15m', 0)
    off_hours = feature_row.get('is_off_hours', 0)
    
    # High failures, targeting many unique users
    if failures > 15 and users > 5:
        return "Credential Stuffing", "T1110.004"
        
    # High failures, targeting a single or few users
    elif failures > 20 and users <= 3:
        return "Brute Force Attack", "T1110.001"
        
    # Low volume, but steady spacing (e.g., failed attempts over long time)
    elif 5 < failures <= 20 and feature_row.get('failure_ratio_15m', 0) > 0.9:
        return "Low and Slow Attack", "T1110.001"
        
    # Successful login during off-hours, possibly an anomaly if unusual
    elif success > 0 and off_hours == 1 and failures == 0:
        return "Anomalous Off-Hour Access", "T1078"
        
    # Default fallback for unknown anomalies
    return "Unknown Anomalous Activity", "T1190"
