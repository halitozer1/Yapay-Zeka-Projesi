from core import Optimizer
import pandas as pd
from datetime import datetime, timedelta

# Mock data
df = pd.DataFrame({
    'timestamp': [datetime.now() - timedelta(hours=i) for i in range(672)],
    'usage_liters': [20] * 672
})
budget = 500.0
water_limit = 30000.0

print("\n--- Testing Diversification (Run 1) ---")
report1 = Optimizer.generate_ai_report(df, budget, water_limit)
for line in report1:
    if "Öneri:" in line: print(line)

print("\n--- Testing Diversification (Run 2) ---")
report2 = Optimizer.generate_ai_report(df, budget, water_limit)
for line in report2:
    if "Öneri:" in line: print(line)

entries = {"2023-10-01": {"total": 1200, "night": 200}}
print("\n--- Testing Manual Diversification (Run 1) ---")
m_report1 = Optimizer.generate_manual_ai_report(entries, budget, water_limit)
for line in m_report1:
    if "Optimizasyon Odağı:" in line: print(line)

print("\n--- Testing Manual Diversification (Run 2) ---")
m_report2 = Optimizer.generate_manual_ai_report(entries, budget, water_limit)
for line in m_report2:
    if "Optimizasyon Odağı:" in line: print(line)
