from datetime import datetime, timedelta
import os
import json
import pandas as pd


# =========================================================
# COST CALCULATOR
# =========================================================
class CostCalculator:
    # ISKI-like approximate tariffs (project uses TL/L)
    UNIT_PRICE_DAY = 0.089705
    UNIT_PRICE_NIGHT = UNIT_PRICE_DAY * 2  # 22:00-04:00 is 2x

    NIGHT_START = 22
    NIGHT_END = 4

    @staticmethod
    def calculate_cost(usage_liters, hour):
        price = CostCalculator.UNIT_PRICE_DAY
        if hour >= CostCalculator.NIGHT_START or hour < CostCalculator.NIGHT_END:
            price = CostCalculator.UNIT_PRICE_NIGHT
        return float(usage_liters) * float(price)

    @staticmethod
    def calculate_period_stats(df, budget, reference_usage, manual_entries, session_system_usage, session_system_cost, session_hours):
        """
        Produces a single metrics dict for the UI.
        This function is intentionally compatible with your existing frontend expectations.
        """
        df = df.copy()
        if not df.empty:
            df["cost"] = df.apply(
                lambda row: CostCalculator.calculate_cost(row["usage_liters"], row["timestamp"].hour),
                axis=1
            )
        else:
            df["cost"] = []

        # --- System totals (window) ---
        total_system_usage_window = float(df["usage_liters"].sum()) if not df.empty else 0.0
        total_system_cost_window = float(df["cost"].sum()) if not df.empty else 0.0
        window_hours = int(len(df))

        # System night usage in window (for savings estimate)
        if not df.empty:
            system_night_usage = float(df[df["timestamp"].dt.hour.isin([22, 23, 0, 1, 2, 3])]["usage_liters"].sum())
        else:
            system_night_usage = 0.0

        # Coverage and projection
        session_days = max(1.0, float(session_hours) / 24.0)
        system_weeks = session_days / 7.0

        if window_hours > 0:
            system_projected_cost = (total_system_cost_window / window_hours) * 720.0
            system_projected_usage = (total_system_usage_window / window_hours) * 720.0
        else:
            system_projected_cost = 0.0
            system_projected_usage = 0.0

        # --- Manual stats ---
        total_manual_usage = 0.0
        total_manual_cost = 0.0
        total_manual_night = 0.0
        manual_daily_usage = {}
        manual_daily_cost = {}

        if manual_entries:
            for date_str, data in manual_entries.items():
                if isinstance(data, dict):
                    usage = float(data.get("total", 0))
                    night = float(data.get("night", 0))
                else:
                    usage = float(data)
                    night = 0.0

                day_usage = usage - night
                cost = (day_usage * CostCalculator.UNIT_PRICE_DAY) + (night * CostCalculator.UNIT_PRICE_NIGHT)

                total_manual_usage += usage
                total_manual_cost += float(cost)
                total_manual_night += night

                manual_daily_usage[date_str] = float(usage)
                manual_daily_cost[date_str] = float(cost)

        manual_days_count = len(manual_entries) if manual_entries else 0
        manual_weeks = manual_days_count / 7.0

        if manual_days_count > 0:
            manual_projected_cost = (total_manual_cost / manual_days_count) * 30.0
            manual_projected_usage = (total_manual_usage / manual_days_count) * 30.0
        else:
            manual_projected_cost = 0.0
            manual_projected_usage = 0.0

        # Baseline comparison
        daily_ref = float(reference_usage) * 24.0
        weekly_ref_cost = daily_ref * session_days * CostCalculator.UNIT_PRICE_DAY

        profit_loss = weekly_ref_cost - (float(session_system_cost) + total_manual_cost)

        manual_ref_cost_total = daily_ref * manual_days_count * CostCalculator.UNIT_PRICE_DAY
        manual_profit_loss = manual_ref_cost_total - total_manual_cost

        # Daily charts (system)
        if not df.empty:
            daily_usage_system = df.groupby(df["timestamp"].dt.date)["usage_liters"].sum().to_dict()
            daily_cost_system = df.groupby(df["timestamp"].dt.date)["cost"].sum().to_dict()
        else:
            daily_usage_system = {}
            daily_cost_system = {}

        res_usage_system = {str(k): float(v) for k, v in daily_usage_system.items()}
        res_cost_system = {str(k): float(v) for k, v in daily_cost_system.items()}

        # Days remaining heuristic (kept consistent with your project)
        days_remaining = max(0.1, (672 - float(session_hours)) / 24.0)

        # Optimization payload (keep keys compatible)
        optimization = Optimizer.calculate_strategy(
            system_stats={
                "total_usage": float(session_system_usage),
                "total_cost": float(session_system_cost),
                "projection": float(system_projected_usage),         # usage projection (legacy key)
                "projected_cost": float(system_projected_cost),      # cost projection (legacy key)
                "night_usage": float(system_night_usage),
                "usage_projection": float(system_projected_usage),   # alias (new, safe)
                "cost_projection": float(system_projected_cost),     # alias (new, safe)
            },
            manual_stats={
                "total_usage": float(total_manual_usage),
                "total_cost": float(total_manual_cost),
                "projection": float(manual_projected_usage),         # usage projection (legacy key)
                "projected_cost": float(manual_projected_cost),      # cost projection (legacy key)
                "total_night_usage": float(total_manual_night),
                "usage_projection": float(manual_projected_usage),   # alias
                "cost_projection": float(manual_projected_cost),     # alias
            },
            budget=float(budget),
            water_limit=float(daily_ref * 30.0),  # derived monthly baseline from reference usage
            reference_usage=float(reference_usage),
            days_remaining=float(days_remaining),
        )

        return {
            "budget": float(budget),
            "system": {
                "total_usage": float(session_system_usage),
                "total_cost": float(session_system_cost),
                "projection": float(system_projected_cost),          # cost projection (UI expects cost projection here)
                "usage_projection": float(system_projected_usage),
                "weeks": round(system_weeks, 1),
                "percent": float((system_projected_cost / budget) * 100 if budget > 0 else 100),
                "is_over": bool(system_projected_cost > budget),
            },
            "manual": {
                "total_usage": float(total_manual_usage),
                "total_cost": float(total_manual_cost),
                "projection": float(manual_projected_cost),          # cost projection
                "usage_projection": float(manual_projected_usage),
                "weeks": round(manual_weeks, 1),
                "percent": float((manual_projected_cost / budget) * 100 if budget > 0 else 100),
                "is_over": bool(manual_projected_cost > budget),
            },
            "analysis": {
                "weekly_delta": float(profit_loss),
                "monthly_delta": float(profit_loss * 4.3),
                "manual_weekly_delta": float(manual_profit_loss),
                "manual_monthly_delta": float(
                    manual_profit_loss * (30 / max(1, manual_days_count)) if manual_days_count > 0 else 0
                ),
            },
            "daily": {
                "usage_system": res_usage_system,
                "cost_system": res_cost_system,
                "usage_manual": manual_daily_usage,
                "cost_manual": manual_daily_cost,
            },
            "optimization": optimization,
        }


# =========================================================
# LINEAR PROGRAMMING CORE (Analytical LP Solution)
# =========================================================
def solve_daily_water_optimization(daily_water_limit, daily_budget, day_price, night_price):
    """
    Linear Programming model (analytical solution)

    Decision variables:
      x1 = daytime water usage (L/day)
      x2 = nighttime water usage (L/day)

    Objective:
      minimize Z = c_d*x1 + c_n*x2

    Constraints:
      x1 + x2 <= daily_water_limit
      c_d*x1 + c_n*x2 <= daily_budget
      x1, x2 >= 0

    Insight:
      If c_n > c_d, optimal shifts as much as possible to daytime (x2 as small as feasible).
      Budget constraint may force x2 down to keep within cost.
    """

    L = max(0.0, float(daily_water_limit))
    B = max(0.0, float(daily_budget))
    cd = float(day_price)
    cn = float(night_price)

    # If prices equal, any allocation is equivalent; choose all daytime.
    if cn <= cd:
        x2 = 0.0
        x1 = min(L, B / cd if cd > 0 else 0.0)
        cost = x1 * cd
        return {"x_day": round(x1, 1), "x_night": round(x2, 1), "min_cost": round(cost, 2)}

    # We want x2 as small as possible while satisfying both constraints.
    # If we insist x1+x2 = L (use full limit), then budget requires:
    # cd*(L - x2) + cn*x2 <= B  ->  cd*L + (cn-cd)*x2 <= B
    # -> x2 <= (B - cd*L)/(cn - cd)
    # Optimal (min cost) wants the smallest x2; but if budget is tight, it constrains feasible total usage.
    # We'll compute:
    #   - If B >= cd*L : can afford full L with x2 = 0 (all daytime)
    #   - If B < cd*L  : cannot afford full L even with all daytime. Then max affordable usage is B/cd, still x2 = 0.
    if cd <= 0:
        return {"x_day": 0.0, "x_night": 0.0, "min_cost": 0.0}

    if B >= cd * L:
        x2 = 0.0
        x1 = L
        cost = x1 * cd
    else:
        # Budget is the binding constraint; buy as much as possible at daytime price (still optimal).
        x2 = 0.0
        x1 = B / cd
        cost = x1 * cd

    return {"x_day": round(x1, 1), "x_night": round(x2, 1), "min_cost": round(cost, 2)}


# =========================================================
# RECOMMENDATION HISTORY (Anti-Repetition)
# =========================================================
class RecommendationHistory:
    """
    Persisted anti-repetition across reports.
    Stored as recommendation_history.json next to this file.
    """

    def __init__(self, max_keep=14):
        self.max_keep = int(max_keep)
        self.path = os.path.join(os.path.dirname(__file__), "recommendation_history.json")
        self.state = {"system": [], "manual": []}
        self._load()

    def _load(self):
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                self.state["system"] = list(data.get("system", []))[: self.max_keep]
                self.state["manual"] = list(data.get("manual", []))[: self.max_keep]
        except Exception:
            self.state = {"system": [], "manual": []}

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    @staticmethod
    def tip_id(text):
        return "tip:" + str(text).strip().lower()

    def recently_used(self, context):
        return set(self.state.get(context, []))

    def add_used(self, context, tips):
        if context not in self.state:
            self.state[context] = []
        ids = [self.tip_id(t) for t in tips]
        new_list = ids + [x for x in self.state[context] if x not in ids]
        self.state[context] = new_list[: self.max_keep]
        self.save()


# =========================================================
# OPTIMIZER + AI RECOMMENDATION ENGINE
# =========================================================
class Optimizer:
    # Expanded, categorized pools (more variety)
    ADVICE_POOLS = {
        "dishwasher": [
            "Bulaşık makinesini 'Eko' modunda çalıştırmak su tüketimini ve faturayı belirgin düşürür.",
            "Bulaşıkları akan su altında ön durulamak yerine sıyırıp makineye yerleştirmek her yıkamada ciddi tasarruf sağlar.",
            "Bulaşık makinesini tam dolmadan çalıştırmayın; yıkama sıklığını azaltmak tüketimi optimize eder.",
            "Yüksek sıcaklık programlarını sadece gerektiğinde kullanın; çoğu gün orta program yeterlidir.",
            "Makinede kısa program her zaman az su demek değildir; eko programı uzun sürse de daha verimlidir.",
            "Filtre temizliği, makinenin verimli çalışmasını sağlar; gereksiz tekrar yıkamayı önler."
        ],
        "laundry": [
            "Çamaşır makinesini sadece tam dolu olduğunda çalıştırarak su ve enerji tasarrufunu maksimize edin.",
            "Çamaşır yıkamayı gündüz saatlerine kaydırmak gece tarifesinden kaçınarak maliyeti düşürür.",
            "Ön yıkamayı sadece gerçekten kirli çamaşırlarda açın; çoğu zaman gereksiz su tüketir.",
            "Aynı sıcaklıkta yıkanabilecek çamaşırları birleştirmek yıkama sayısını azaltır.",
            "Kısa program suyu azaltmıyor olabilir; eko programı deneyin.",
            "Deterjanı doğru dozda kullanmak, yeniden durulama ihtiyacını düşürür."
        ],
        "shower": [
            "Duş süresini 2 dakika kısaltmak ay sonunda fark edilir tasarruf sağlar.",
            "Sabunlanırken suyu kapatmak her duşta onlarca litreyi kurtarır.",
            "Tasarruflu duş başlığı, aynı konforda daha düşük debi sağlar.",
            "Gece duş alıyorsanız gündüze kaydırmak aynı suyu daha ucuza kullanmanızı sağlar.",
            "Sıcak suyu gereksiz yükseltmek hem su hem enerji maliyetini artırır.",
            "Duşta kademeli aç/kapa yerine sabit akış kullanmak tüketimi kontrol etmeyi kolaylaştırır."
        ],
        "garden": [
            "Bahçeyi gün doğumunda sulamak buharlaşmayı azaltır; aynı su daha verimli kullanılır.",
            "Damla sulama sistemleri hortuma göre çok daha verimlidir.",
            "Sulama süresini ölçüp standartlaştırın; göz kararı genelde fazla suya kaçıyor.",
            "Bitki diplerine malç sererek toprağın nemini daha uzun koruyabilirsiniz.",
            "Yağmur sonrası sulamayı ertelemek gereksiz tüketimi önler.",
            "Hortum yerine kova ile temizlik/sulama çoğu zaman daha az su harcatır."
        ],
        "general": [
            "Musluk ve rezervuar sızıntılarını kontrol edin; küçük damlama bile haftada ciddi litreye çıkar.",
            "Sebze-meyveyi akan su altında değil bir kapta yıkamak su israfını azaltır.",
            "Diş fırçalarken musluğu kapatmak küçük ama sürekli tasarruf sağlar.",
            "Sayaç takibini haftada bir yapmak tüketim artışını erken yakalatır.",
            "Atık su bedeli kullanım ile orantılıdır; az kullanım çift taraflı tasarruftur.",
            "Elde bulaşık yıkıyorsanız leğen kullanmak sürekli akan suya göre çok daha verimlidir."
        ]
    }

    @staticmethod
    def _deterministic_seed_from_df(df):
        try:
            if df is None or df.empty:
                return "no_data"
            return str(df.iloc[-1]["timestamp"])
        except Exception:
            return "fallback_seed"

    @staticmethod
    def _pick_diverse_tips(categories, seed, context, k=2):
        """
        Picks k tips with anti-repetition across reports.
        Deterministic shuffle with seed, but history can affect final selection.
        """
        import random
        rng = random.Random(seed)
        history = RecommendationHistory(max_keep=14)
        used = history.recently_used(context)

        candidates = []
        for cat in categories:
            for tip in Optimizer.ADVICE_POOLS.get(cat, []):
                candidates.append((cat, tip))

        rng.shuffle(candidates)

        chosen = []
        chosen_ids = set()

        # Pass 1: avoid recent history
        for _, tip in candidates:
            tid = RecommendationHistory.tip_id(tip)
            if tid in used:
                continue
            if tid in chosen_ids:
                continue
            chosen.append(tip)
            chosen_ids.add(tid)
            if len(chosen) >= k:
                break

        # Pass 2: allow repeats if needed (still avoid duplicates in same report)
        if len(chosen) < k:
            for _, tip in candidates:
                tid = RecommendationHistory.tip_id(tip)
                if tid in chosen_ids:
                    continue
                chosen.append(tip)
                chosen_ids.add(tid)
                if len(chosen) >= k:
                    break

        history.add_used(context, chosen)
        return chosen

    @staticmethod
    def generate_ai_report(df, budget, water_limit):
        """
        SYSTEM (simulation) report:
        - keeps your existing output style (List[str])
        - adds LP-based optimal target lines
        - uses diverse + anti-repeating tips
        """
        if df is None or df.empty:
            return ["Henüz analiz için yeterli veri oluşmadı. Simülasyon devam ettikçe buradayım!"]

        df = df.copy()

        # Weekly slicing (168h each)
        weekly_stats = []
        target_weekly_usage = water_limit / 4.0

        seed = Optimizer._deterministic_seed_from_df(df)
        import random
        rng = random.Random(seed)

        for i in range(4):
            start_idx = i * 168
            end_idx = (i + 1) * 168
            week_df = df.iloc[start_idx:end_idx].copy()

            if week_df.empty:
                weekly_stats.append(None)
                continue

            week_df["cost"] = week_df.apply(
                lambda row: CostCalculator.calculate_cost(row["usage_liters"], row["timestamp"].hour),
                axis=1
            )
            usage = float(week_df["usage_liters"].sum())
            cost = float(week_df["cost"].sum())
            delta_l = float(target_weekly_usage - usage)
            weekly_stats.append({"usage": usage, "cost": cost, "delta_l": delta_l})

        valid = [s for s in weekly_stats if s]
        total_usage = float(sum(s["usage"] for s in valid)) if valid else 0.0
        total_cost = float(sum(s["cost"] for s in valid)) if valid else 0.0

        # Night usage ratio (for AI reasoning)
        night_usage = float(df[df["timestamp"].dt.hour.isin([22, 23, 0, 1, 2, 3])]["usage_liters"].sum())
        night_ratio = (night_usage / total_usage) if total_usage > 0 else 0.0

        # LP optimal daily targets (döküman uyumu)
        daily_water_limit = float(water_limit) / 30.0
        daily_budget = float(budget) / 30.0
        lp = solve_daily_water_optimization(
            daily_water_limit=daily_water_limit,
            daily_budget=daily_budget,
            day_price=CostCalculator.UNIT_PRICE_DAY,
            night_price=CostCalculator.UNIT_PRICE_NIGHT
        )

        lines = []
        greetings = [
            "Selam! Bu ayki su kullanımını analiz ettim.",
            "Merhaba! Su tüketim verilerin geldi; hadi birlikte bakalım.",
            "Rapor hazır! Bu ay hedeflerle aramız nasıl, görelim.",
            "Selam, bu ayki performansı mercek altına aldım."
        ]
        lines.append(rng.choice(greetings))
        lines.append("Analiz sonuçların şöyle:")

        # Weekly breakdown (human-like)
        for idx, stats in enumerate(weekly_stats):
            w_idx = idx + 1
            if not stats:
                lines.append(f"💤 {w_idx}. hafta verilerini henüz beklemedeyiz.")
                continue

            diff = abs(stats["delta_l"])
            if stats["delta_l"] < 0:
                msgs = [
                    f"⚠️ {w_idx}. hafta hedefi {diff:.0f}L aştık; burada biraz sıkılaşalım.",
                    f"⚠️ {w_idx}. hafta yoğun geçmiş; limitin {diff:.0f}L üstündeyiz.",
                    f"⚠️ {w_idx}. hafta su tüketimi hedefin {diff:.0f}L üzerinde."
                ]
                lines.append(rng.choice(msgs))
            else:
                msgs = [
                    f"✅ {w_idx}. hafta hedefin {diff:.0f}L altında. Süper!",
                    f"✅ {w_idx}. hafta {diff:.0f}L tasarruf var. Böyle devam.",
                    f"✅ {w_idx}. hafta gayet iyi: {diff:.0f}L aşağıdasın."
                ]
                lines.append(rng.choice(msgs))

        # Budget summary
        profit_loss = float(budget) - total_cost
        saved_water = float(water_limit) - total_usage

        if profit_loss > 0:
            lines.append(f"🎉 Bütçeye göre {profit_loss:.2f} TL artıdasın.")
        else:
            lines.append(f"📉 Bütçe hedefinden {abs(profit_loss):.2f} TL saptık.")

        if saved_water > 0:
            lines.append(f"🌍 Toplamda {saved_water:.0f}L su tasarrufu yaptın.")
        else:
            lines.append(f"🌍 Bu ay {abs(saved_water):.0f}L limit üstü kullanım var.")

        # LP reference lines (optimization-backed AI)
        lines.append("🔢 Optimizasyon Modeli (LP) Referansı:")
        lines.append(f"• Günlük ideal gündüz kullanım (x1): {lp['x_day']} L/gün")
        lines.append(f"• Günlük ideal gece kullanım (x2): {lp['x_night']} L/gün")
        lines.append(f"• Günlük minimum maliyet: {lp['min_cost']} ₺/gün")

        # AI reasoning around night ratio
        if night_ratio > 0.35:
            lines.append(f"🤖 Gece kullanım oranın %{night_ratio*100:.0f}. Gece tarifesi pahalı olduğu için burası en hızlı kazanç noktası.")
        else:
            lines.append(f"🤖 Gece kullanım oranın %{night_ratio*100:.0f}. Bu oldukça iyi; maliyet avantajı sağlıyor.")

        # Diverse + anti-repeating tips
        lines.append("💡 Tekrar etmeyen önerilerim:")

        categories = ["general", "shower", "dishwasher", "laundry"]
        if total_usage > water_limit:
            categories.append("garden")

        tips = Optimizer._pick_diverse_tips(categories=categories, seed=seed, context="system", k=2)
        for t in tips:
            lines.append(f"• {t}")

        closings = [
            "Her damla geleceğimiz için bir yatırım. Devam.",
            "Bu farkındalıkla devam edersen hem dünya hem bütçe kazanır.",
            "Tasarruf yolculuğunda yanındayım; yeni veriler gelince daha da netleşir."
        ]
        lines.append(rng.choice(closings))
        return lines

    @staticmethod
    def generate_manual_ai_report(manual_entries, budget, water_limit):
        """
        MANUAL report:
        - keeps existing output style (List[str])
        - uses diverse + anti-repeating tips
        - adds LP-based ideal day/night guidance (reference)
        """
        if not manual_entries:
            return ["Henüz manuel veri girişi yapılmadı. Lütfen sayaç veya fatura verilerinizi giriniz."]

        sorted_dates = sorted(manual_entries.keys(), reverse=True)
        last_7_dates = sorted_dates[:7]
        latest_date = sorted_dates[0]

        total_usage_7 = 0.0
        total_cost_7 = 0.0
        total_night_usage_7 = 0.0

        for d in last_7_dates:
            entry = manual_entries[d]
            usage = float(entry.get("total", 0)) if isinstance(entry, dict) else float(entry)
            night = float(entry.get("night", 0)) if isinstance(entry, dict) else 0.0
            day_usage = usage - night
            cost = (day_usage * CostCalculator.UNIT_PRICE_DAY) + (night * CostCalculator.UNIT_PRICE_NIGHT)
            total_usage_7 += usage
            total_cost_7 += float(cost)
            total_night_usage_7 += night

        num_days = len(last_7_dates)
        target_weekly_usage = float(water_limit) / 4.0
        target_weekly_budget = float(budget) / 4.0

        daily_avg_usage = total_usage_7 / num_days if num_days > 0 else 0.0
        daily_avg_cost = total_cost_7 / num_days if num_days > 0 else 0.0
        monthly_projection_usage = daily_avg_usage * 30.0
        monthly_projection_cost = daily_avg_cost * 30.0

        usage_diff = total_usage_7 - target_weekly_usage
        cost_diff = total_cost_7 - target_weekly_budget

        manual_seed = "-".join(sorted(manual_entries.keys())) + f"|{latest_date}"

        import random
        rng = random.Random(manual_seed)

        # LP reference for manual (daily targets)
        daily_water_limit = float(water_limit) / 30.0
        daily_budget = float(budget) / 30.0
        lp = solve_daily_water_optimization(
            daily_water_limit=daily_water_limit,
            daily_budget=daily_budget,
            day_price=CostCalculator.UNIT_PRICE_DAY,
            night_price=CostCalculator.UNIT_PRICE_NIGHT
        )

        # Night share
        night_ratio = (total_night_usage_7 / total_usage_7) if total_usage_7 > 0 else 0.0

        lines = []
        openers = [
            "Manuel kullanım raporunu çıkardım. Net konuşacağım:",
            "Manuel verilerini analiz ettim. Şu tablo var:",
            "Sayaç/fatura girişlerine göre kısa bir özet:",
            "Manuel girişlere göre durum değerlendirmesi yaptım:"
        ]
        lines.append(rng.choice(openers))
        lines.append(f"Son girdiğiniz {latest_date} verisi dahil (son {num_days} gün) analiz edildi.")

        if usage_diff > 0:
            lines.append(f"• Su Kullanımı: Haftalık hedefin {usage_diff:.0f}L üzerindesiniz.")
        else:
            lines.append(f"• Su Kullanımı: Haftalık hedefin {abs(usage_diff):.0f}L altındasınız. İyi gidiyor.")

        usage_status = "hedefin üzerinde" if monthly_projection_usage > water_limit else "hedefin altında"
        lines.append(f"• Aylık Öngörü: Bu tempoyla ~{monthly_projection_usage/1000:.2f} m³ bekleniyor ({usage_status}).")

        if cost_diff > 0:
            lines.append(f"• Bütçe: Haftalık bütçe hedefini {cost_diff:.2f} TL aşıyorsunuz.")
        else:
            lines.append(f"• Bütçe: Haftayı {abs(cost_diff):.2f} TL avantajla kapatıyorsunuz.")

        cost_status = "bütçe aşımı riski var" if monthly_projection_cost > budget else "bütçe dahilinde"
        lines.append(f"• Finansal Öngörü: Ay sonu ~{monthly_projection_cost:.2f} ₺ ({cost_status}).")

        # LP reference lines
        lines.append("🔢 Optimizasyon Modeli (LP) Referansı:")
        lines.append(f"• Günlük ideal gündüz kullanım (x1): {lp['x_day']} L/gün")
        lines.append(f"• Günlük ideal gece kullanım (x2): {lp['x_night']} L/gün")
        lines.append(f"• Günlük minimum maliyet: {lp['min_cost']} ₺/gün")

        if night_ratio > 0.35:
            lines.append(f"🤖 Gece kullanım oranınız %{night_ratio*100:.0f}. En hızlı tasarruf, gece tüketimini gündüze kaydırmaktır.")
        else:
            lines.append(f"🤖 Gece kullanım oranınız %{night_ratio*100:.0f}. Gece tarafı gayet kontrollü görünüyor.")

        # Diverse + non-repeating tips
        lines.append("💡 Önerilerim:")

        categories = ["general", "laundry", "dishwasher", "shower"]
        if total_usage_7 > target_weekly_usage:
            categories.append("garden")

        tips = Optimizer._pick_diverse_tips(categories=categories, seed=manual_seed, context="manual", k=2)
        for t in tips:
            lines.append(f"• {t}")

        
        
        return lines

    @staticmethod
    def sustainable_impact(saved_water_liters, budget_benefit=0):
        """
        Environmental impact summary used in UI.
        """
        is_saving = saved_water_liters >= 0
        abs_water = abs(saved_water_liters)

        co2_saved_kg = (saved_water_liters / 1000.0) * 0.3
        trees = abs(co2_saved_kg) / 1.6
        contribution_pc = (saved_water_liters / 30000.0) * 100.0

        if budget_benefit >= 0:
            benefit_text = f"Bütçenize {budget_benefit:.2f} ₺ tasarruf katkısı sağlandı."
        else:
            benefit_text = f"Bütçe hedefiniz {abs(budget_benefit):.2f} ₺ aşıldı."

        if is_saving:
            text = f"Tasarruf: {trees:.2f} ağaçlık CO2 emilimi dengelendi. {abs_water:.0f}L su tasarrufu yapıldı. {benefit_text}"
        else:
            text = f"Aşım: {trees:.2f} ağaçlık CO2 emilimi kapasitesi aşıldı. {abs_water:.0f}L limit üstü kullanım. {benefit_text}"

        return {
            "text": text,
            "percentage": float(max(-100, min(100, contribution_pc))),
            "trees": round(trees, 2),
            "water": round(saved_water_liters, 1),
            "benefit": round(budget_benefit, 2),
            "is_saving": is_saving
        }

    @staticmethod
    def calculate_strategy(system_stats, manual_stats, budget, water_limit, reference_usage, days_remaining):
        """
        Strategy card computation.
        Kept compatible, but made more robust with aliases.
        """
        # Remaining budget/water (based on accumulated totals)
        rem_budget = float(budget) - (float(system_stats.get("total_cost", 0.0)) + float(manual_stats.get("total_cost", 0.0)))
        rem_water = float(water_limit) - (float(system_stats.get("total_usage", 0.0)) + float(manual_stats.get("total_usage", 0.0)))

        daily_water_target = max(0.0, rem_water / float(days_remaining)) if days_remaining > 0 else 0.0
        daily_budget_target = max(0.0, rem_budget / float(days_remaining)) if days_remaining > 0 else 0.0

        # Tariff shift potential
        total_night_usage = float(system_stats.get("night_usage", 0.0)) + float(manual_stats.get("total_night_usage", 0.0))
        potential_savings = total_night_usage * (CostCalculator.UNIT_PRICE_NIGHT - CostCalculator.UNIT_PRICE_DAY)

        # Ratios (support both legacy and alias keys)
        usage_proj = float(system_stats.get("usage_projection", system_stats.get("projection", 0.0))) + float(manual_stats.get("usage_projection", manual_stats.get("projection", 0.0)))
        cost_proj = float(system_stats.get("cost_projection", system_stats.get("projected_cost", 0.0))) + float(manual_stats.get("cost_projection", manual_stats.get("projected_cost", 0.0)))

        usage_ratio = usage_proj / float(water_limit) if float(water_limit) > 0 else 1.0
        cost_ratio = cost_proj / float(budget) if float(budget) > 0 else 1.0

        score = 100.0 - (max(usage_ratio, cost_ratio) - 1.0) * 100.0

        if score > 95:
            status = "Mükemmel"
        elif score > 80:
            status = "Dengeli"
        elif score > 50:
            status = "Dikkatli Olmalı"
        else:
            status = "Kritik Eşik"

        return {
            "daily_water_target": round(daily_water_target, 1),
            "daily_budget_target": round(daily_budget_target, 2),
            "potential_savings": round(potential_savings, 2),
            "status": status,
            "score": round(max(0.0, min(100.0, score)), 1),
            "days_remaining": round(float(days_remaining), 1)
        }
