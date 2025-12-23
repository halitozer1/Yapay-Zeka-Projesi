from core import Optimizer, CostCalculator

# Sample manual entries (total, night)
entries = {
    "2023-10-01": {"total": 1200, "night": 200},
    "2023-10-02": {"total": 1100, "night": 150},
    "2023-10-03": {"total": 1300, "night": 300},
    "2023-10-04": {"total": 1250, "night": 250},
    "2023-10-05": {"total": 1150, "night": 100},
    "2023-10-06": {"total": 1400, "night": 400},
    "2023-10-07": {"total": 1200, "night": 200},
}

budget = 500.0
water_limit = 30000.0

report = Optimizer.generate_manual_ai_report(entries, budget, water_limit)

print("\n--- Manual AI Recommendation Report ---\n")
for line in report:
    print(line)
