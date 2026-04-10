import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import scipy.stats as stats
import os

# Ensure the figures directory exists
os.makedirs('docs/figures2', exist_ok=True)

# -------------------------------------------------------------------
# 1. Data Ingestion Layer Configuration (Stacked Bar Chart / Scaling plot)
# -------------------------------------------------------------------
def generate_fig11():
    labels = ['Single Node', 'Multi-Threaded', 'Kafka Queue', 'Load Balanced Cluster']
    eps = [1200, 4500, 15000, 50000]
    plt.figure(figsize=(10, 6))
    sns.barplot(x=labels, y=eps, palette='mako')
    plt.title('FIGURE 11 - Data Ingestion Layer Configuration: EPS Scalability', pad=15, fontsize=14, fontweight='bold')
    plt.ylabel('Events Per Second Capacity (EPS)')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.savefig('docs/figures2/fig11_ingestion.png', dpi=300, bbox_inches='tight')
    plt.close()

# -------------------------------------------------------------------
# 2. Log Parsing and Normalization Configuration (Violin Plot for Latency)
# -------------------------------------------------------------------
def generate_fig12():
    np.random.seed(42)
    data_raw = np.random.normal(50, 15, 1000)
    data_regex = np.random.normal(25, 5, 1000)
    data_optimized = np.random.normal(8, 2, 1000)
    plt.figure(figsize=(10, 6))
    sns.violinplot(data=[data_raw, data_regex, data_optimized], palette='Set2')
    plt.xticks([0, 1, 2], ['Raw String Matching', 'Standard Regex Parsing', 'Pre-compiled Regex (Optimized Config)'])
    plt.title('FIGURE 12 - Log Parsing and Normalization Configuration Latencies', pad=15, fontsize=14, fontweight='bold')
    plt.ylabel('Processing Latency (ms)')
    plt.savefig('docs/figures2/fig12_parsing.png', dpi=300, bbox_inches='tight')
    plt.close()

# -------------------------------------------------------------------
# 3. Feature Engineering and Baselining Configuration (Time-series Bands)
# -------------------------------------------------------------------
def generate_fig13():
    np.random.seed(123)
    days = np.arange(30)
    base = 100 + 10 * np.sin(days / 2)
    noise = np.random.normal(0, 5, 30)
    actual = base + noise
    std = np.std(actual)
    upper_bound = base + 2.5 * std
    lower_bound = base - 2.5 * std
    
    plt.figure(figsize=(12, 5))
    plt.plot(days, actual, label='Actual Metric (e.g. Daily Login Frequency)', marker='o', color='#34495e')
    plt.plot(days, base, label='Computed Baseline (Moving Average)', color='#27ae60', lw=2)
    plt.fill_between(days, lower_bound, upper_bound, alpha=0.2, color='#e74c3c', label='Dynamic Configured Threshold (+/- 2.5σ)')
    plt.title('FIGURE 13 - Feature Engineering & Baselining Configuration over 30 Days', pad=15, fontsize=14, fontweight='bold')
    plt.xlabel('Days')
    plt.legend()
    plt.savefig('docs/figures2/fig13_base.png', dpi=300, bbox_inches='tight')
    plt.close()

# -------------------------------------------------------------------
# 4. Detection Engine Component Configuration (Radar Chart)
# -------------------------------------------------------------------
def generate_fig14():
    labels=np.array(['CPU Threshold', 'RAM Threshold', 'GPU Threshold', 'IOPS Target', 'Latency Ceiling'])
    stats_stat = [80, 60, 20, 90, 40]
    stats_ml = [40, 90, 80, 50, 70]
    
    angles=np.linspace(0, 2*np.pi, len(labels), endpoint=False)
    # close the plot
    stats_s=np.concatenate((stats_stat,[stats_stat[0]]))
    stats_m=np.concatenate((stats_ml,[stats_ml[0]]))
    angles=np.concatenate((angles,[angles[0]]))
    
    fig, ax = plt.subplots(figsize=(8,8), subplot_kw=dict(polar=True))
    ax.plot(angles, stats_s, 'o-', linewidth=2, label='Statistical Engine Config Profile')
    ax.fill(angles, stats_s, alpha=0.25)
    ax.plot(angles, stats_m, 'o-', linewidth=2, label='ML/Deep Learning Config Profile')
    ax.fill(angles, stats_m, alpha=0.25)
    ax.set_thetagrids(angles[:-1] * 180/np.pi, labels)
    plt.title('FIGURE 14 - Detection Engine Component Configuration Targets', y=1.1, fontsize=14, fontweight='bold')
    ax.legend(loc='lower left', bbox_to_anchor=(0.9, 0.9))
    plt.savefig('docs/figures2/fig14_engine.png', dpi=300, bbox_inches='tight')
    plt.close()

# -------------------------------------------------------------------
# 5. Configuring Statistical Detection (Z-Score) (Bell Curve)
# -------------------------------------------------------------------
def generate_fig15():
    x = np.linspace(-4, 4, 1000)
    y = stats.norm.pdf(x, 0, 1)
    
    plt.figure(figsize=(10, 6))
    plt.plot(x, y, color='black', lw=2)
    
    # Shade Z > 2.75
    threshold = 2.75
    px = np.arange(threshold, 4, 0.01)
    plt.fill_between(px, stats.norm.pdf(px,0,1), color='#e74c3c', alpha=0.6, label=f'Alert Threshold (Z > {threshold})')
    
    # Shade normal area
    px_norm = np.arange(-4, threshold, 0.01)
    plt.fill_between(px_norm, stats.norm.pdf(px_norm,0,1), color='#ecf0f1', alpha=0.4)

    plt.axvline(threshold, color='#c0392b', linestyle='--', lw=2)
    plt.text(threshold+0.1, 0.2, f'Configured Strict\nZ-Score Threshold = {threshold}', color='#c0392b', fontweight='bold')
    plt.title('FIGURE 15 - Configuring Statistical Detection: Z-Score Distributions', pad=15, fontsize=14, fontweight='bold')
    plt.ylabel('Distribution Density')
    plt.xlabel('Z-Score Deviation')
    plt.legend()
    plt.savefig('docs/figures2/fig15_zscore.png', dpi=300, bbox_inches='tight')
    plt.close()

# -------------------------------------------------------------------
# 6. ML Initial Configuration (ROC Tuning curves)
# -------------------------------------------------------------------
def generate_fig16():
    depths = np.arange(1, 26)
    rf_acc = 0.65 + 0.32 * (1 - np.exp(-0.25 * depths))
    lgbm_acc = 0.62 + 0.35 * (1 - np.exp(-0.18 * depths))
    
    plt.figure(figsize=(10, 6))
    plt.plot(depths, rf_acc, label='Random Forest ROC-AUC', marker='o', markersize=4, color='#2980b9')
    plt.plot(depths, lgbm_acc, label='LightGBM ROC-AUC', marker='s', markersize=4, color='#8e44ad')
    
    # Optimal cutoff
    plt.axvline(12, linestyle='--', color='#2c3e50', alpha=0.7)
    plt.text(12.5, 0.75, 'Configured Maximum Depth Limit = 12\n(Prevents Overfitting)', color='#2c3e50')
    
    plt.title('FIGURE 16 - Initial Configuration & Hyperparameter Tuning of Machine Learning Models', pad=15, fontsize=14, fontweight='bold')
    plt.xlabel('Max Depth Configuration')
    plt.ylabel('ROC-AUC Score (Validation)')
    plt.legend()
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.savefig('docs/figures2/fig16_ml.png', dpi=300, bbox_inches='tight')
    plt.close()

# -------------------------------------------------------------------
# 7. Enabling Ensemble Voting System (Stacked True Pos / False Pos chart)
# -------------------------------------------------------------------
def generate_fig17():
    models = ['Z-Score Alone', 'RF Alone', 'LGBM Alone', 'Autoencoder Alone', 'Ensemble Config']
    true_pos = np.array([800, 910, 930, 890, 955])
    false_pos = np.array([300, 160, 145, 210, 42]) # Ensemble aggressively cuts false positives
    
    ind = np.arange(len(models))
    width = 0.6
    
    plt.figure(figsize=(10, 6))
    p1 = plt.bar(ind, true_pos, width, color='#2ecc71', label='True Positives (Accurate Captures)')
    p2 = plt.bar(ind, false_pos, width, bottom=true_pos, color='#e74c3c', label='False Positives (Noise)')
    
    plt.title('FIGURE 17 - Enabling the Ensemble Voting System: Signal-to-Noise Ratio Config', pad=15, fontsize=14, fontweight='bold')
    plt.ylabel('Total Incident Alerts Generated')
    plt.xticks(ind, models)
    plt.legend()
    plt.savefig('docs/figures2/fig17_ensemble.png', dpi=300, bbox_inches='tight')
    plt.close()

# -------------------------------------------------------------------
# 8. Analysis and Alerting Component (Trigger Tuning Heatmap)
# -------------------------------------------------------------------
def generate_fig18():
    np.random.seed(5)
    data = np.random.poisson(3, (7, 24))
    # Configure weekends to generate fewer alerts based on rules
    data[5:] = np.random.poisson(0.5, (2, 24))
    # Known configured spike at 9 AM due to login rushes
    data[:, 9] += np.random.poisson(5, 7)
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    plt.figure(figsize=(12, 5))
    sns.heatmap(data, cmap='YlOrRd', yticklabels=days, cbar_kws={'label': 'Alert Output Volume'})
    plt.title('FIGURE 18 - Analysis and Alerting Configuration: Trigger Volume Heatmap', pad=15, fontsize=14, fontweight='bold')
    plt.xlabel('Hour of Day (Configured Rulesets)')
    plt.ylabel('Day of Week')
    plt.savefig('docs/figures2/fig18_alerting.png', dpi=300, bbox_inches='tight')
    plt.close()

# -------------------------------------------------------------------
# 9. Security Controls and System Protection Configuration (Donut Chart)
# -------------------------------------------------------------------
def generate_fig19():
    fig, ax = plt.subplots(figsize=(8, 6))
    
    categories = ['TLS 1.3 Target Rate\n(Accepted)', 'TLS 1.2 Backwards Compat\n(Accepted)', 'Unencrypted HTTP\n(Blocked config)', 'Unauthorized Access\n(RBAC Dropped/Blocked)']
    rates = [5500, 1200, 400, 150]
    colors = ['#27ae60', '#f1c40f', '#e74c3c', '#d35400']
    
    wedges, texts, autotexts = ax.pie(rates, labels=categories, autopct='%1.1f%%', startangle=140, colors=colors, 
                                      textprops={'fontsize': 10}, pctdistance=0.85, 
                                      wedgeprops=dict(width=0.4, edgecolor='w'))
    
    ax.set_title('FIGURE 19 - Security Controls & System Protection Configuration', pad=15, fontsize=14, fontweight='bold')
    plt.savefig('docs/figures2/fig19_security.png', dpi=300, bbox_inches='tight')
    plt.close()

# -------------------------------------------------------------------
# 10. Scalability & Performance Config (Dual Axis curve)
# -------------------------------------------------------------------
def generate_fig20():
    nodes = np.arange(1, 11)
    throughput = 12000 * nodes * 0.85 # sublinear
    latency = 8 + 1.5 * np.exp(0.3 * nodes)
    
    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()
    
    ax1.bar(nodes, throughput, color='#3498db', alpha=0.7, label='Scalability Throughput Threshold')
    ax2.plot(nodes, latency, 'r-o', lw=3, label='System Latency Target Curve')
    
    ax1.set_xlabel('Active Scaling Units (Nodes)')
    ax1.set_ylabel('Configured Throughput (EPS)', color='#2980b9')
    ax2.set_ylabel('Target Latency Limit (ms)', color='#c0392b')
    plt.title('FIGURE 20 - Scalability and Performance Considerations Configuration', pad=15, fontsize=14, fontweight='bold')
    
    # Combine legends
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc='upper left')
    
    plt.xticks(nodes)
    plt.savefig('docs/figures2/fig20_scalability.png', dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == '__main__':
    print("Generating Figure 11...")
    generate_fig11()
    print("Generating Figure 12...")
    generate_fig12()
    print("Generating Figure 13...")
    generate_fig13()
    print("Generating Figure 14...")
    generate_fig14()
    print("Generating Figure 15...")
    generate_fig15()
    print("Generating Figure 16...")
    generate_fig16()
    print("Generating Figure 17...")
    generate_fig17()
    print("Generating Figure 18...")
    generate_fig18()
    print("Generating Figure 19...")
    generate_fig19()
    print("Generating Figure 20...")
    generate_fig20()
    print("All Part 2 figures generated successfully in docs/figures2/!")
