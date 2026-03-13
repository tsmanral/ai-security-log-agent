import pandas as pd
from typing import Dict, Any

def extract_behavioral_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract behavioral features tracking host/user interactions from logs.
    
    Args:
        df: DataFrame containing 'timestamp', 'src_ip', 'username', 'event_type'
            
    Returns:
        DataFrame populated with windowed behavioral metrics.
    """
    if df.empty or 'src_ip' not in df.columns or 'username' not in df.columns:
        return df
        
    df = df.copy()
    df = df.sort_values('timestamp')
    
    # Define success/failure flags
    df['is_failure'] = df['event_type'].str.startswith('failed').astype(int)
    df['is_success'] = df['event_type'].str.startswith('accepted').astype(int)
    
    # Temporary index for rolling operations
    df_temp = df.set_index('timestamp').copy()
    
    # Group by src_ip and calculate rolling metrics over a time window (e.g., 5 minutes)
    # Total attempts from this IP in the last 5 minutes
    ip_stats = df_temp.groupby('src_ip').rolling('5min').agg({
        'is_failure': 'sum',
        'is_success': 'sum',
        'event_type': 'count' # total events
    }).reset_index()
    
    # We need to map this back to original df
    # Since rolling preserves the index, we can just grab it
    # However, multi-index (src_ip, timestamp) might be complex to merge directly
    
    # An easier feature mapping approach for the agent:
    # 1. Number of distinct usernames targeted by this IP in the last 15 mins
    import numpy as np
    
    # We need to map username to a numeric ID because pandas rolling.apply fails on object arrays
    df_temp['username_id'] = pd.factorize(df_temp['username'])[0]
    
    def count_unique(series):
        # Using raw=True passes numpy arrays, so we use np.unique
        return len(np.unique(series[~np.isnan(series)]))
        
    user_diversity = df_temp.groupby('src_ip')['username_id'].rolling('15min').apply(count_unique, raw=True).reset_index(name='unique_users_15m')
    
    # Failures and success in 15m
    activity_15m = df_temp.groupby('src_ip').rolling('15min').agg({
        'is_failure': 'sum',
        'is_success': 'sum'
    }).reset_index()
    
    activity_15m = activity_15m.rename(columns={
        'is_failure': 'failures_15m',
        'is_success': 'successes_15m'
    })
    
    # Merge the calculated features back into df by matching 'src_ip' and 'timestamp'
    # We'll need a unique id or merge on ip/timestamp exactly
    df = pd.merge_asof(
        df.sort_values('timestamp'), 
        user_diversity.sort_values('timestamp'), 
        on='timestamp', by='src_ip'
    )
    
    df = pd.merge_asof(
        df.sort_values('timestamp'), 
        activity_15m.sort_values('timestamp'), 
        on='timestamp', by='src_ip'
    )
    
    # Derived features
    # Failure ratio
    df['failure_ratio_15m'] = df['failures_15m'] / (df['failures_15m'] + df['successes_15m'] + 1e-9)
    
    return df
