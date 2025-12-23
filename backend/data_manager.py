import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import hashlib
import json

class DataManager:
    def __init__(self):
        self.csv_path = os.path.join(os.path.dirname(__file__), 'usage_real.csv')
        self.full_data = self._load_data()
        self.budget = 500.0  # Default budget in TL
        self.reference_usage = 41.67 # Updated reference to 30m3/mo (41.67L/h)
        self.monthly_water_limit = 30000.0
        self.manual_json_path = os.path.join(os.path.dirname(__file__), 'manual_entries.json')
        self.report_json_path = os.path.join(os.path.dirname(__file__), 'latest_report.json')
        self.manual_entries = self._load_manual_entries()
        self.latest_report = self._load_latest_report()
        
        # Cache for manual recommendations
        self._manual_recommendations_cache = None
        self._manual_entries_hash = self._compute_manual_hash()
        
        # Simulation cursor - MUST be initialized BEFORE get_simulation_window is called
        self.stream_index = 0
        self.session_system_usage = 0.0
        self.session_system_cost = 0.0
        self.session_manual_usage = 0.0
        self.session_manual_cost = 0.0
        self.session_hours = 0  # Track elapsed hours for projection
        
        # If no persisted report exists, generate an initial one from current window
        if not self.latest_report and not self.full_data.empty:
            try:
                from core import Optimizer
                self.latest_report = Optimizer.generate_ai_report(
                    self.get_simulation_window(672),
                    self.budget,
                    self.monthly_water_limit
                )
                self.save_latest_report(self.latest_report)
            except Exception as e:
                print(f"DEBUG: Initial report generation failed: {e}")
        
    def _load_manual_entries(self):
        if os.path.exists(self.manual_json_path):
            try:
                import json
                with open(self.manual_json_path, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _load_latest_report(self):
        if os.path.exists(self.report_json_path):
            try:
                import json
                with open(self.report_json_path, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_latest_report(self, report_lines):
        import json
        self.latest_report = report_lines
        with open(self.report_json_path, 'w') as f:
            json.dump(report_lines, f)

    def _save_manual_entries(self):
        with open(self.manual_json_path, 'w') as f:
            json.dump(self.manual_entries, f)
        # Invalidate cache when entries change
        self._manual_entries_hash = self._compute_manual_hash()
        self._manual_recommendations_cache = None
    
    def _compute_manual_hash(self):
        """Compute a hash of manual entries to detect changes."""
        data_str = json.dumps(self.manual_entries, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def get_cached_manual_recommendations(self):
        """Get manual recommendations from cache, regenerating only if data changed."""
        current_hash = self._compute_manual_hash()
        
        # Return cached if hash matches and cache exists
        if self._manual_recommendations_cache is not None and current_hash == self._manual_entries_hash:
            return self._manual_recommendations_cache
        
        # Regenerate recommendations
        from core import Optimizer
        self._manual_recommendations_cache = Optimizer.generate_manual_ai_report(
            self.manual_entries,
            self.budget,
            self.monthly_water_limit
        )
        self._manual_entries_hash = current_hash
        return self._manual_recommendations_cache
    
    def invalidate_manual_cache(self):
        """Force invalidation of manual recommendations cache."""
        self._manual_recommendations_cache = None
            
    def _load_data(self):
        if not os.path.exists(self.csv_path):
            return pd.DataFrame(columns=['timestamp', 'usage_liters'])
            
        df = pd.read_csv(self.csv_path, comment='#')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        return df

    def get_simulation_window(self, hours=168):
        """
        Returns a data window of 'hours' ending at the current stream_index.
        Handles wrap-around if the simulation is near the beginning.
        """
        end_idx = self.stream_index
        num_rows = len(self.full_data)
        
        if hours >= num_rows:
            return self.full_data.copy()
            
        if end_idx >= hours:
            window = self.full_data.iloc[end_idx - hours:end_idx].copy()
        else:
            # Wrap around: take from end of df and from start
            remaining = hours - end_idx
            part1 = self.full_data.iloc[num_rows - remaining:]
            part2 = self.full_data.iloc[:end_idx]
            window = pd.concat([part1, part2])
            
        return window

    def advance_simulation(self, hours=672):
        """
        Jump forward in the simulation, accumulating statistics for the skipped period.
        """
        from core import CostCalculator
        
        num_rows = len(self.full_data)
        current_idx = self.stream_index
        target_idx = (current_idx + hours) % num_rows
        
        # Calculate usage and cost for the skipped interval
        skipped_usage = 0
        skipped_cost = 0
        
        # If wrap around
        if target_idx < current_idx:
            subset1 = self.full_data.iloc[current_idx:]
            subset2 = self.full_data.iloc[:target_idx]
            combined = pd.concat([subset1, subset2])
        else:
            combined = self.full_data.iloc[current_idx:target_idx]
            
        for _, row in combined.iterrows():
            u = row['usage_liters']
            h = row['timestamp'].hour
            c = CostCalculator.calculate_cost(u, h)
            skipped_usage += u
            skipped_cost += c
            
        self.session_system_usage += skipped_usage
        self.session_system_cost += skipped_cost
        self.session_hours += hours
        
        self.stream_index = target_idx
        print(f"DEBUG: Simulation advanced by {hours} hours. Usage added: {skipped_usage:.2f}L, Cost added: {skipped_cost:.2f} TL")

    def complete_current_period(self, target_hours=672):
        """
        Advances simulation to complete the current 4-week cycle.
        Returns the number of hours advanced.
        """
        if self.session_hours == 0:
            remaining = target_hours
        else:
            remainder = self.session_hours % target_hours
            if remainder == 0:
                remaining = target_hours # Already at end, advance full cycle
            else:
                remaining = target_hours - remainder
        
        self.advance_simulation(hours=remaining)
        return remaining

    def start_new_period(self):
        """
        Resets period statistics to start a fresh tracking cycle.
        """
        self.session_system_usage = 0.0
        self.session_system_cost = 0.0
        self.session_hours = 0
        # self.manual_entries = {}  # REMOVED: Keep manual entries across periods
        # self._save_manual_entries() # REMOVED: No need to save if not changed
        print("DEBUG: New period started. System usage and cost stats reset. Manual data preserved.")

    def add_manual_entry(self, date_str, amount, night_amount=0):
        """
        Validates date format and adds usage to the stored manual entries.
        amount: total liters
        night_amount: liters used between 22:00-04:00
        """
        # Validate date format
        datetime.strptime(date_str, "%Y-%m-%d")
        
        # We store as a dict per date
        self.manual_entries[date_str] = {
            "total": float(amount),
            "night": float(night_amount)
        }
        self._save_manual_entries()
        print(f"DEBUG: Added {amount}L (Night: {night_amount}L) to {date_str}.")

    def delete_manual_entry(self, date_str):
        if date_str in self.manual_entries:
            del self.manual_entries[date_str]
            self._save_manual_entries()
            return True
        return False
            
    def set_budget(self, amount):
        from core import CostCalculator
        self.budget = float(amount)
        # Calculate water limit based on budget: "Param kadar su"
        # Since Day price is the baseline, Limit = Budget / Price
        self.monthly_water_limit = self.budget / CostCalculator.UNIT_PRICE_DAY
        # Update hourly reference
        self.reference_usage = self.monthly_water_limit / (30.0 * 24.0)
        # Invalidate cache since budget affects recommendations
        self.invalidate_manual_cache()
        print(f"DEBUG: New Budget: {self.budget}₺ -> Master Water Limit: {self.monthly_water_limit:.1f}L")

    def set_water_limit(self, amount):
        # We keep this for external calls, but it will be secondary to set_budget in the UI
        self.monthly_water_limit = float(amount)
        self.reference_usage = self.monthly_water_limit / (30.0 * 24.0)
        
    def get_current_simulation_tick(self):
        """
        Returns a moving window of data to simulate 'flow'.
        Includes manual usage if available for the date.
        """
        window_size = 24
        total_len = len(self.full_data)
        
        if total_len < window_size:
            return self.full_data.to_dict(orient='records')
            
        # Move cursor
        self.stream_index = (self.stream_index + 1) % total_len
        
        # Get window
        start = self.stream_index
        end = start + window_size
        
        if end < total_len:
            window = self.full_data.iloc[start:end].copy()
        else:
            part1 = self.full_data.iloc[start:]
            part2 = self.full_data.iloc[:(end - total_len)]
            window = pd.concat([part1, part2])
            
        now = datetime.now()
        timestamps = [now - timedelta(hours=window_size - i - 1) for i in range(window_size)]
        window['timestamp'] = timestamps
        
        # Accumulate the LATEST point from the window into session stats
        # (Assuming the simulation advances by one point each time this is called)
        latest_point = window.iloc[-1]
        usage_val = latest_point['usage_liters']
        hour_val = latest_point['timestamp'].hour
        
        # We need CostCalculator here. Since DataManager is often imported by main, 
        # Let's do it inside the method or use a callback.
        from core import CostCalculator
        cost_val = CostCalculator.calculate_cost(usage_val, hour_val)
        
        self.session_system_usage += usage_val
        self.session_system_cost += cost_val
        self.session_hours += 1  # Each tick = 1 hour

        # Add manual usage column
        def get_manual(ts):
            date_key = ts.strftime("%Y-%m-%d")
            entry = self.manual_entries.get(date_key, None)
            if entry is None:
                return 0
            if isinstance(entry, dict):
                return entry.get("total", 0) / 24.0
            return float(entry) / 24.0

        window['manual_usage'] = window['timestamp'].apply(get_manual)
        
        # Detect if we just completed a cycle
        is_cycle_end = (self.stream_index == total_len - 1)
        
        return window.to_dict(orient='records'), is_cycle_end

data_store = DataManager()
