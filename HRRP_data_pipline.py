"""
CMS Hospital Readmissions Reduction Program (HRRP) - Data Pipeline
====================================================================
Loads, cleans, and prepares CMS HRRP data for Power BI dashboard visualization.
Outputs a clean CSV ready for Power BI import with calculated fields.

Data Source: CMS Hospital Readmissions Reduction Program (2025)
https://data.cms.gov/provider-data/dataset/9n3s-kdb3

Author: Brianna Foreman
"""

import numpy as np 
import pandas as pd 

# =============================================================
# 1. LOAD DATA
# =============================================================
print("Loading CMS HRRP data...")
df = pd.read_csv('FY_2025_Hospital_Readmissions_Reduction_Program_Hospital.csv')
print(f"   Loaded {len(df):,} rows across {df['Facility ID'].nunique():,} hospitals\n")
# =============================================================
# 2. DATA CLEANING
# =============================================================
print("Cleaning data...")

# Remove rows with missing critical fields
initial_count = len(df)
df = df.dropna(subset=['Excess Readmission Ratio', 'Number of Discharges'])
print(f"   Removed {initial_count - len(df)} rows with missing values")

# Ensure numeric types
numeric_cols = ['Facility ID', 'Number of Discharges',
                'Excess Readmission Ratio', 'Predicted Readmission Rate', 
                'Expected Readmission Rate', 'Number of Readmissions']
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# =============================================================
# 3. CALCULATED FIELDS
# =============================================================
print("\nCreating calculated fields...")

# Penalty flag
df['Is Penalized'] = (df['Excess Readmission Ratio'] > 1.0).astype(int)

# Performance category
def categorize_performance(err):
    if err <= 0.90:
        return 'Significantly Better'
    elif err <= 1.00:
        return 'Better Than Expected'
    elif err <= 1.05:
        return 'Slightly Worse'
    elif err <= 1.10:
        return 'Worse Than Expected'
    else:
        return 'Significantly Worse'
    
df['Performance Category'] = df['Excess Readmission Ratio'].apply(categorize_performance)

# Readmission rate (observed)
df['Observed Readmission Rate'] = (
    df['Number of Readmissions'] / df['Number of Discharges']
).round(4)

# Map condition to measure name
conditions = { 
            "READM-30-AMI-HRRP": "Heart Attack", 
            "READM-30-CABG-HRRP": "CABG",
            "READM-30-COPD-HRRP": "COPD",
            "READM-30-HF-HRRP": "Heart Failure",
            "READM-30-HIP-KNEE-HRRP": "THA/TKA",
            "READM-30-PN-HRRP": "Pneumonia"
            }
df['Condition'] = df['Measure Name'].map(conditions)

region_map = {
    'CT': 'Northeast', 'ME': 'Northeast', 'MA': 'Northeast', 'NH': 'Northeast',
    'RI': 'Northeast', 'VT': 'Northeast', 'NJ': 'Northeast', 'NY': 'Northeast', 'PA': 'Northeast',
    'IL': 'Midwest', 'IN': 'Midwest', 'MI': 'Midwest', 'OH': 'Midwest', 'WI': 'Midwest',
    'IA': 'Midwest', 'KS': 'Midwest', 'MN': 'Midwest', 'MO': 'Midwest', 'NE': 'Midwest',
    'ND': 'Midwest', 'SD': 'Midwest',
    'DE': 'South', 'FL': 'South', 'GA': 'South', 'MD': 'South', 'NC': 'South',
    'SC': 'South', 'VA': 'South', 'WV': 'South', 'AL': 'South', 'KY': 'South',
    'MS': 'South', 'TN': 'South', 'AR': 'South', 'LA': 'South', 'OK': 'South', 'TX': 'South',
    'AZ': 'West', 'CO': 'West', 'ID': 'West', 'MT': 'West', 'NV': 'West',
    'NM': 'West', 'UT': 'West', 'WY': 'West', 'AK': 'West', 'CA': 'West',
    'HI': 'West', 'OR': 'West', 'WA': 'West',
}
df['Region'] = df['State'].map(region_map).fillna('Territories')

# Calculate Percentages
df['Observed Readmission Rate Pct'] = (df['Observed Readmission Rate'] * 100).round(1)
df['Is Penalized Pct'] = df['Is Penalized'] * 100

# =============================================================
# 4. SUMMARY STATISTICS
# =============================================================
print("\n" + "="*60)
print("DATASET SUMMARY")
print("\n" + "="*60)
print(f"   Total records:    {len(df):,}")
print(f"   Unique Hospitals:    {df['Facility ID'].nunique():,}")
print(f"   States and Territories Represented:    {df['State'].nunique():,}")
print(f"   Conditions Tracked:    {df['Measure Name'].nunique():,}")

print(f"\n   Hospitals with penalties: {df.groupby('Facility ID')['Is Penalized'].max().sum():,}")
print(f"   Avg Excess Readmission Ratio: {df['Excess Readmission Ratio'].mean():,}")

print("\n   Readmission Rates by Condition:")
for cond in sorted(df['Condition'].unique()):
    subset = df[df['Condition'] == cond]
    print(f"   {cond:8s} Avg ERR = {subset['Excess Readmission Ratio'].mean():.4f}, "
          f"Avg Observed Rate = {subset['Observed Readmission Rate'].mean():.3f}, "
          f"N = {len(subset):,}")


print("\n   Performance Distribution")
for cat in ['Significantly Better', 'Better Than Expected', 'Slightly Worse', 
            'Worse Than Expected', 'Significantly Worse']:
    count = len(df[df['Performance Category'] == cat])
    pct = count / len(df) * 100
    print(f"   {cat:25s}: {count:,} ({pct:.1f}%)")
# =============================================================
# 5. EXPORT CLEAN DATA
# =============================================================
output_file = 'cms_hrrp_dashboard_data.csv'
df.to_csv(output_file, index=False)
print(f"Clean dataset exported to: {output_file}")
print(f"   {len(df):,} rows x {len(df.columns)} columns\n")
print("Columns: ")
for idx, col in enumerate(list(df.columns)):
    print(f"   {idx + 1}: {col}")