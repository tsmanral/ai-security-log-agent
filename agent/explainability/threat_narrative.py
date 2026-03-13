from typing import Dict, Any, List

class ThreatNarrativeGenerator:
    """
    Generates human-readable narratives explaining why an event was flagged 
    as anomalous, using rule-based templates and feature importance lists.
    """
    
    # Mapping feature names to human-readable descriptors
    FEATURE_DESCRIPTIONS = {
        'failures_15m': "the high number of authentication failures ({} times) in the last 15 minutes",
        'successes_15m': "the number of successful logins ({} times) in the last 15 minutes",
        'failure_ratio_15m': "an unusually high percentage of failing login attempts",
        'time_since_last_event_ip': "the rapid succession of connections from this IP",
        'unique_users_15m': "targeting a high number of unique accounts ({} users)",
        'is_off_hours': "occurring during known off-hours for this system",
        'is_weekend': "occurring during the weekend when activity is usually low",
        'hour_sin': "the irregular time of day",
        'hour_cos': "the irregular time of day"
    }

    @staticmethod
    def generate_narrative(
        is_anomaly: bool, 
        threat_type: str, 
        mitre_tactic: str,
        top_features: List[str],
        row_data: Dict[str, Any]
    ) -> str:
        """
        Generate a narrative string based on the threat context.
        
        Args:
            is_anomaly: Whether the model flagged this.
            threat_type: The classified threat type (e.g., 'Brute Force').
            mitre_tactic: The associated MITRE ATT&CK ID.
            top_features: The list of top feature names from SHAP.
            row_data: The actual log and feature values.
            
        Returns:
            A string explaining the alert.
        """
        if not is_anomaly:
            return "Activity appears normal based on historical baselines."
            
        ip = row_data.get('src_ip', 'Unknown IP')
        user = row_data.get('username', 'Unknown User')
        
        # Base intro
        narrative = f"A {threat_type} attack ({mitre_tactic}) was detected from IP address {ip} targeting user '{user}'. "
        
        # Add explanation of why, based on SHAP features
        if top_features:
            reasons = []
            for feat in top_features[:3]:
                desc = ThreatNarrativeGenerator.FEATURE_DESCRIPTIONS.get(feat, f"an anomaly in {feat}")
                
                # Try to format with the actual value if the placeholder exists
                if "{}" in desc:
                    val = row_data.get(feat, 'multiple')
                    # Format float to int if needed
                    if isinstance(val, float):
                        val = int(val)
                    try:
                        desc = desc.format(val)
                    except:
                        pass
                reasons.append(desc)
                
            if len(reasons) > 1:
                reason_str = ", ".join(reasons[:-1]) + f", and {reasons[-1]}"
            else:
                reason_str = reasons[0]
                
            narrative += f"The AI ensemble flagged this activity primarily due to {reason_str}. "
            
        # Add contextual advice
        if threat_type == "Brute Force":
            narrative += "Recommend temporarily blocking the source IP."
        elif threat_type == "Credential Stuffing":
            narrative += "Ensure multi-factor authentication (MFA) is enabled for targeted accounts."
        elif threat_type == "Off-Hour Access":
            narrative += "Verify if this access was scheduled or authorized."
            
        return narrative
