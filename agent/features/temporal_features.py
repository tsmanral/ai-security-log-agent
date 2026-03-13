import pandas as pd
import numpy as np
from typing import Dict, Any

def extract_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract temporal features from a dataframe of parsed logs.
    
    Args:
        df: DataFrame containing at least 'timestamp' column and a unique index
        
    Returns:
        DataFrame with added temporal features.
    """
    if df.empty or 'timestamp' not in df.columns:
        return df
        
    df = df.copy()
    
    # Ensure timestamp is datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Basic time components
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['minute'] = df['timestamp'].dt.minute
    
    # Cyclic encoding for time of day to handle the wrap-around (23:59 -> 00:00)
    # Hour is mapped onto a circle using sin/cos
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24.0)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24.0)
    
    # Is it off-hours? (e.g. 10 PM to 6 AM)
    df['is_off_hours'] = df['hour'].apply(lambda x: 1 if (x < 6 or x >= 22) else 0)
    df['is_weekend'] = df['day_of_week'].apply(lambda x: 1 if x >= 5 else 0)
    
    # Calculate login velocity (events per time window)
    # We will use rolling windows to count events in past N minutes
    
    df = df.sort_values('timestamp')
    
    # Time deltas between events from same IP
    if 'src_ip' in df.columns:
        # Time since last event from this IP
        df['time_since_last_event_ip'] = df.groupby('src_ip')['timestamp'].diff().dt.total_seconds().fillna(0)
    
    return df
