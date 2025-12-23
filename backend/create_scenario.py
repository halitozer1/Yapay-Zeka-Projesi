import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

def generate_water_data():
    # Scenario Definition (4 Months / 16 Weeks)
    # N=Normal (~900L/day), H=High (~2200L/day to ensure over limit)
    # Monthly Limit: 30,000L. Weekly target ~7,000L.
    
    scenario_weeks = [
        # Month 1: Weeks 2 and 3 are HIGH
        'normal', 'high', 'high', 'normal',
        # Month 2: All NORMAL (Perfect month)
        'normal', 'normal', 'normal', 'normal',
        # Month 3: Week 4 is HIGH
        'normal', 'normal', 'normal', 'high',
        # Month 4: Week 1 is HIGH
        'high', 'normal', 'normal', 'normal'
    ]
    
    # Start date doesn't strictly matter for simulation logic but good to be recent
    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    data_rows = []
    
    current_time = start_date
    
    print(f"Generating data for {len(scenario_weeks)} weeks...")
    
    # Target Calculations
    monthly_limit = 30000.0
    weekly_limit = monthly_limit / 4.0 # 7500L
    
    # Daily targets
    # Normal: ~7200L/week -> ~1028L/day
    # High: ~7800L/week (Limit + 300L) -> ~1114L/day
    
    print(f"Generating data for {len(scenario_weeks)} weeks. Weekly Limit: {weekly_limit}L")
    
    for i, week_type in enumerate(scenario_weeks):
        # Determine target weekly total based on type
        if week_type == 'high':
             # Overage between 120L and 500L
            overage = random.uniform(120, 500)
            target_total = weekly_limit + overage
        else:
             # Under limit (saving) between 100L and 600L
            saving = random.uniform(100, 600)
            target_total = weekly_limit - saving
            
        # Target daily average for this week
        daily_target = target_total / 7.0
        
        # 7 days per week
        for day in range(7):
            # Distribute daily target into 24 hours
            # We need a profile that sums up to ~daily_target
            
            # Profile weights (sum of weights for 24h)
            # 0-6: 1
            # 7-9: 4
            # 10-17: 2
            # 18-22: 5
            # 23: 1
            # Total weight units approx: (7*1) + (3*4) + (8*2) + (5*5) + (1*1) = 7+12+16+25+1 = 61 units
            
            # Unit value = daily_target / 61
            unit_val = daily_target / 61.0
            
            for hour in range(24):
                if 0 <= hour < 7:
                    weight = 1 
                elif 7 <= hour < 10:
                    weight = 4
                elif 10 <= hour < 18:
                    weight = 2
                elif 18 <= hour < 23:
                    weight = 5
                else:
                    weight = 1
                
                base_usage = weight * unit_val
                
                # Add small randomness (+- 10%) so it's not robotic
                usage = base_usage * random.uniform(0.9, 1.1)
                
                data_rows.append({
                    'timestamp': current_time,
                    'usage_liters': usage
                })
                current_time += timedelta(hours=1)
        
        print(f"Week {i+1} ({week_type}) generated. Target: {target_total:.1f}L")

    df = pd.DataFrame(data_rows)
    
    # Save to CSV
    output_path = os.path.join(os.path.dirname(__file__), 'usage_real.csv')
    df.to_csv(output_path, index=False)
    print(f"Data saved to {output_path}. Total rows: {len(df)}")

if __name__ == "__main__":
    generate_water_data()
