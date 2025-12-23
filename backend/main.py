from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import pandas as pd
from datetime import datetime

# Import local modules
from data_manager import data_store
from core import CostCalculator, Optimizer

app = FastAPI(title="Water AI Optimization")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class BudgetRequest(BaseModel):
    amount: float

class ManualUsageRequest(BaseModel):
    date: str # YYYY-MM-DD
    amount: float
    night_amount: float = 0.0

class WaterLimitRequest(BaseModel):
    amount: float

@app.get("/")
def read_root():
    return {"status": "ok", "service": "Water AI Optimization Backend"}

@app.get("/metrics")
def get_metrics():
    """
    Returns calculated metrics for the dashboard.
    """
    recent_data = data_store.get_simulation_window(hours=168) # 7 days
    stats = CostCalculator.calculate_period_stats(
        recent_data, 
        data_store.budget, 
        data_store.reference_usage,
        manual_entries=data_store.manual_entries,
        session_system_usage=data_store.session_system_usage,
        session_system_cost=data_store.session_system_cost,
        session_hours=max(1, data_store.session_hours)  # Prevent division by zero
    )

    # Calculate savings/sustainability (Projected monthly impact)
    monthly_limit = data_store.monthly_water_limit
    
    # Use PROJECTED usage for sustainability to match dashboard "Tahmini" logic
    projected_total_usage = stats['system']['usage_projection'] + stats['manual']['usage_projection']
    saved_water = monthly_limit - projected_total_usage

    # Financial benefit (profit/loss)
    # Aligning this with the BudgetPanel logic: Budget - Projecton
    benefit = data_store.budget - (stats['system']['projection'] + stats['manual']['projection'])
    
    sustainability = Optimizer.sustainable_impact(saved_water, budget_benefit=benefit)

    # Manual specific sustainability (Projected for 30 days)
    manual_projected_usage = stats['manual']['usage_projection']
    manual_saved_projection = monthly_limit - manual_projected_usage
    manual_benefit_projection = data_store.budget - stats['manual']['projection']
    manual_sustainability = Optimizer.sustainable_impact(manual_saved_projection, budget_benefit=manual_benefit_projection)

    return {
        "stats": stats,
        "sustainability": sustainability,
        "manual_sustainability": manual_sustainability,
        "budget": data_store.budget,
        "monthly_water_limit": data_store.monthly_water_limit,
        "manual_entries": data_store.manual_entries,
        "recommendations": data_store.latest_report,
        "manual_recommendations": data_store.get_cached_manual_recommendations()
    }

@app.get("/stream")
def get_stream():
    """
    Returns the latest window of data for the real-time graph.
    Now includes 'cost' for each data point.
    """
    data, is_end = data_store.get_current_simulation_tick()
    
    if is_end:
        from core import Optimizer
        new_report = Optimizer.generate_ai_report(
            data_store.get_simulation_window(672),
            data_store.budget,
            data_store.monthly_water_limit
        )
        data_store.save_latest_report(new_report)

    enriched_data = []
    for point in data:
        status = 'equal'
        usage_val = point['usage_liters']
        if usage_val > data_store.reference_usage:
            status = 'high'
        elif usage_val < data_store.reference_usage:
            status = 'low'

        # Calculate hourly cost
        # Point['timestamp'] is a datetime object or string?
        # DataManager converts it to string in to_dict() if not careful,
        # but get_current_simulation_tick uses datetime objects in the dataframe.
        # However, to_dict(orient='records') usually converts them to ISO strings or keep them.
        # Let's ensure we parse if string.
        ts = point['timestamp']
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        
        cost_val = CostCalculator.calculate_cost(usage_val, ts.hour)
            
        enriched_data.append({
            **point,
            'usage': usage_val,
            'cost': float(cost_val),
            'status': status,
            'reference': data_store.reference_usage
        })
        
    return enriched_data

@app.get("/recommendations")
def get_recommendations():
    """
    Returns AI suggestions based on simulation data.
    """
    recent_data = data_store.get_simulation_window(672) # 4 weeks
    tips = Optimizer.generate_ai_report(
        recent_data, 
        data_store.budget, 
        data_store.monthly_water_limit
    )
    return {"recommendations": tips}

@app.post("/simulation/skip")
def skip_simulation():
    # Advance to end of month (complete the cycle)
    hours_advanced = data_store.complete_current_period()
    
    # Generate report for the COMPLETED month
    new_report = Optimizer.generate_ai_report(
        data_store.get_simulation_window(672),
        data_store.budget,
        data_store.monthly_water_limit
    )
    data_store.save_latest_report(new_report)
    
    return {"status": "success", "advanced_hours": float(hours_advanced), "period_completed": True}

@app.post("/simulation/resume")
def resume_simulation():
    # Reset stats for new month
    data_store.start_new_period()
    # Clear report
    data_store.save_latest_report(["Yeni dönem başladı. Veri toplanıyor..."])
    return {"status": "success", "message": "New period started"}

@app.post("/budget")
def set_budget(budget: BudgetRequest):
    data_store.set_budget(budget.amount)
    return {"status": "success", "new_budget": budget.amount}

@app.post("/usage/manual")
def add_manual_usage(entry: ManualUsageRequest):
    try:
        data_store.add_manual_entry(entry.date, entry.amount, entry.night_amount)
        return {"status": "success", "message": "Manual entry added"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/usage/manual/{date_str}")
def delete_manual_usage(date_str: str):
    success = data_store.delete_manual_entry(date_str)
    if success:
        return {"status": "success", "message": "Record deleted"}
    raise HTTPException(status_code=404, detail="Record not found")

@app.post("/limit/water")
def set_water_limit(limit: WaterLimitRequest):
    data_store.set_water_limit(limit.amount)
    return {"status": "success", "new_limit": limit.amount}

# =============================================================================
# FAQ DATABASE - 25 Comprehensive Q&A Pairs
# =============================================================================
FAQ_DATABASE = [
    {
        "keywords": ["nereden başla", "başlangıç", "ilk adım", "nasıl başla", "ne yapmalı", "başlamak"],
        "question": "Günlük hayatta su tasarrufu yapmak için nereden başlamalıyım?",
        "answer": """Aslında bu soru çok yerinde, çünkü çoğu kişi nereden başlayacağını bilemediği için hiçbir şey yapmamayı tercih ediyor. 

En doğru başlangıç noktası, gün içinde en sık yaptığın su kullanım alışkanlıklarını fark etmek. Özellikle duş süresi, çamaşır ve bulaşık yıkama sıklığı genelde en fazla suyun harcandığı alanlar oluyor. 

Burada yapacağın küçük değişiklikler bile kısa sürede fark edilir sonuçlar doğurur. 💧"""
    },
    {
        "keywords": ["en çok harca", "nereye gidiyor", "tespit", "hangi alan", "çok su", "nerede harcan"],
        "question": "En çok su harcadığım alanları nasıl tespit edebilirim?",
        "answer": """Bunu anlamanın birkaç basit yolu var. 

Öncelikle günlük rutinini düşün: duş, mutfak, çamaşır, temizlik… Sonra aylık su faturandaki artış ve azalışlara bak. 

Genellikle en çok su; uzun duşlar, sık çamaşır yıkama ve akan su altında yapılan mutfak işlerinden gider. Bunları fark etmek, tasarrufun ilk adımıdır. 📊"""
    },
    {
        "keywords": ["farkında olmadan", "israf", "bilinçsiz", "fark etmeden", "habersiz"],
        "question": "Evde farkında olmadan yaptığım su israfı ne olabilir?",
        "answer": """Çoğu zaman fark edilmeden yapılan israf, aslında en büyük kayıplara neden olur. 

Damlatan bir musluk, sızdıran bir rezervuar ya da gereksiz yere açık bırakılan su, gün sonunda ciddi miktarlara ulaşabilir. 

Bunlar küçük gibi görünür ama uzun vadede büyük etki yaratır. Bir damla bile günde 20 litre kayıp demek! 💧"""
    },
    {
        "keywords": ["fatura", "yansı", "para", "maliyet", "ne kadar düş", "tasarruf et"],
        "question": "Su tasarrufu gerçekten faturaya ne kadar yansır?",
        "answer": """Evet, düşündüğünden daha fazla yansır! 

Düzenli ve bilinçli su tasarrufu yapan bir hanede faturalar genellikle %15 ila %30 arasında düşer. 

Bu da hem aylık bütçene katkı sağlar hem de gereksiz tüketimin önüne geçer. Küçük değişiklikler, büyük tasarruflar demek! 💰"""
    },
    {
        "keywords": ["küçük değişiklik", "alışkanlık", "ufak", "basit", "kolay", "anlamlı fark"],
        "question": "Küçük alışkanlık değişiklikleri gerçekten anlamlı bir fark yaratır mı?",
        "answer": """Kesinlikle evet! 

Örneğin duş süresini sadece birkaç dakika kısaltmak ya da makineleri tam dolmadan çalıştırmamak, ay sonunda binlerce litre su tasarrufu anlamına gelir. 

Küçük görünen değişiklikler, birleştiğinde büyük fark yaratır. Her damla önemli! 🌊"""
    },
    {
        "keywords": ["duş süre", "kısalt", "duş tasarruf", "dakika", "duşta ne kadar"],
        "question": "Duş süresini kısaltırsam ne kadar su tasarrufu sağlarım?",
        "answer": """Ortalama bir duşta dakikada yaklaşık 10-15 litre su harcanır. 

Yani duş süreni 5 dakika kısalttığında tek seferde 50 ila 75 litre arasında su tasarrufu yapmış olursun. 

Bunu ay boyunca düşündüğünde ciddi bir kazanç ortaya çıkar: Ayda yaklaşık 1.500-2.000 litre! 🚿"""
    },
    {
        "keywords": ["sabunlan", "kapat aç", "duşta kapat", "ara ver"],
        "question": "Duş alırken suyu kapatıp açmak mantıklı mı?",
        "answer": """Evet, kesinlikle mantıklı! 

Sabunlanma sırasında suyu kapatmak, gereksiz akışı önler. Bu alışkanlık duş sırasında harcadığın suyu neredeyse yarı yarıya azaltabilir. 

Her duşta 20-30 litre tasarruf demek bu! 💧"""
    },
    {
        "keywords": ["tasarruflu duş başlığı", "az su tüketen", "duş başlığı", "verimli başlık"],
        "question": "Daha az su tüketen duş başlıkları gerçekten işe yarıyor mu?",
        "answer": """Bu konuda çok soru geliyor ama cevabı net: Evet, işe yarıyor! 

Tasarruflu duş başlıkları suyu daha verimli dağıtır ve %30-50 oranında daha az su tüketilmesini sağlar. 

Üstelik duş konforundan da ödün vermezsin. Yatırımın kendini kısa sürede amorti eder! 🚿"""
    },
    {
        "keywords": ["gün aşırı", "her gün duş", "sıklık", "kaç kez duş"],
        "question": "Günlük duş yerine gün aşırı duş almak ne kadar tasarruf sağlar?",
        "answer": """Bu tamamen kişisel ihtiyaçlara bağlı ama duş sıklığını azaltmak doğal olarak su tüketimini de düşürür. 

Hijyen koşullarını koruyarak yapılan bu değişiklik, aylık tüketimde ciddi bir fark yaratabilir. 

Örneğin 30 yerine 15 duş = yarı yarıya tasarruf! 🌊"""
    },
    {
        "keywords": ["elde mi makine", "bulaşık makine", "elde yıka", "hangisi tasarruflu"],
        "question": "Bulaşıkları elde mi yoksa makinede mi yıkamak daha tasarruflu?",
        "answer": """Tam dolu çalışan bir bulaşık makinesi, elde yıkamaya göre çok daha az su tüketir. 

Makine: 12-15 litre
Elde (akan su): 30-40 litre

Özellikle akan su altında elde yıkamak, en fazla israfa neden olan yöntemlerden biridir. Makineyi tercih et ama tam dolu çalıştır! 🍽️"""
    },
    {
        "keywords": ["sebze meyve", "yıka", "meyve yıkama", "sebze yıkama"],
        "question": "Sebze ve meyveleri yıkarken suyu nasıl daha verimli kullanabilirim?",
        "answer": """Akan su yerine bir kap içinde yıkamak en pratik ve tasarruflu yöntemdir. 

Bu şekilde hem suyu boşa akıtmamış olursun hem de ihtiyacın kadar su kullanırsın. 

Aynı su ile birden fazla meyve/sebze yıkayabilirsin! 🥗"""
    },
    {
        "keywords": ["çamaşır makine", "hangi koşul", "tam dolu", "yarım yük"],
        "question": "Çamaşır makinesini hangi koşullarda çalıştırmak daha az su harcatır?",
        "answer": """Makinenin tam dolu çalıştırılması ve doğru programın seçilmesi en verimli yöntemdir. 

Yarım yükte çalıştırılan makineler, gereksiz su ve enerji tüketimine neden olur. Çünkü makine aynı suyu kullanır!

Sabırlı ol, dolmasını bekle. 🧺"""
    },
    {
        "keywords": ["ön yıkama", "prewash", "ön durulama"],
        "question": "Ön yıkama yapmamak gerçekten fark yaratır mı?",
        "answer": """Evet, ön yıkama ciddi miktarda ekstra su tüketir. 

Çamaşırlar aşırı kirli değilse ön yıkamadan kaçınmak hem su hem enerji tasarrufu sağlar. 

Çoğu modern deterjan zaten ön yıkamaya gerek kalmadan temizlik sağlar. 🧼"""
    },
    {
        "keywords": ["belirli saat", "hangi saat", "zaman", "ne zaman kullan"],
        "question": "Suyu günün belirli saatlerinde kullanmak neden önemli?",
        "answer": """Bazı saatlerde su talebi daha yoğundur ve bu hem maliyeti hem de sistem üzerindeki yükü artırır. 

Özellikle gece tarifesi (22:00-04:00) 2 kat pahalı olduğu için bu saatlerden kaçınmak önemli!

Kullanımı gün içine dengeli yaymak, hem bütçe hem altyapı açısından daha verimlidir. ⏰"""
    },
    {
        "keywords": ["gece kullanım", "gece su", "neden önerilmiyor"],
        "question": "Gece su kullanımı neden bazen önerilmiyor?",
        "answer": """İki önemli sebep var:

1️⃣ Gece tarifesi gündüzün 2 katı pahalı (22:00-04:00)
2️⃣ Gece sürekli ve plansız su akışı bazen tesisat kaçağına işaret edebilir

Bu yüzden gece kullanımı kontrol altında tutulmalı ve düzenli olmalıdır. 🌙"""
    },
    {
        "keywords": ["saat değiştir", "zaman değiştir", "ne kazanırım"],
        "question": "Duş, çamaşır ve bulaşık saatlerini değiştirirsem ne kazanırım?",
        "answer": """Daha dengeli bir tüketim profili oluşturursun. 

Bu hem faturayı kontrol etmene yardımcı olur hem de su sistemlerinin daha sağlıklı çalışmasına katkı sağlar.

Özellikle gece tarifesinden (22:00-04:00) kaçınarak ciddi tasarruf yapabilirsin! 💰"""
    },
    {
        "keywords": ["çevre", "doğa", "katkı", "ekoloji", "yeşil"],
        "question": "Su tasarrufu yaparsam çevreye ne gibi katkım olur?",
        "answer": """Su tasarrufu, sadece bireysel bir kazanç değil; aynı zamanda çevreye doğrudan bir katkıdır. 

Su kaynaklarının korunmasına ve ekosistemin sürdürülebilirliğine destek olursun.

Her litre tasarruf, gelecek nesillere bırakılan bir miras! 🌍"""
    },
    {
        "keywords": ["sürdürülebilir", "uzun vade", "gelecek"],
        "question": "Su tüketimini azaltmak sürdürülebilirlik açısından neden önemli?",
        "answer": """Tatlı su kaynakları sınırlıdır. Dünya'daki suyun sadece %2.5'i tatlı su!

Bugün kontrollü kullanım, yarının su güvenliği demektir. 

Bu nedenle sürdürülebilirlik açısından kritik bir konudur. Her damla değerli! 💧"""
    },
    {
        "keywords": ["aşırı kullanım", "sorun", "risk", "tehlike"],
        "question": "Aşırı su kullanımı uzun vadede ne gibi sorunlara yol açar?",
        "answer": """Ciddi sonuçları var:

• Su kıtlığı riski
• Artan faturalar ve maliyetler  
• Altyapı sorunları
• Çevresel tahribat

Bu da hem bireysel hem toplumsal risk anlamına gelir. Şimdiden önlem almak şart! ⚠️"""
    },
    {
        "keywords": ["iklim", "karbon", "sera gazı", "küresel ısınma"],
        "question": "Su tasarrufu yapmak gerçekten iklim değişikliğiyle bağlantılı mı?",
        "answer": """Evet, doğrudan bağlantılı!

Su arıtımı ve dağıtımı enerji gerektirir. Daha az su tüketimi, dolaylı olarak daha az enerji kullanımı ve karbon salımı demektir.

Her litre tasarruf = daha az karbon ayak izi! 🌱"""
    },
    {
        "keywords": ["takip", "izle", "davranış değiş", "ölç"],
        "question": "Su tüketimimi takip edersem davranışlarım nasıl değişir?",
        "answer": """Tüketimi görmek farkındalık yaratır. 

İnsanlar genellikle ölçtükleri şeyi daha dikkatli kullanır ve bu da doğal olarak tasarrufa yol açar.

'Ölçemediğin şeyi yönetemezsin' derler, bu tam da öyle! 📊"""
    },
    {
        "keywords": ["haftalık analiz", "rapor", "istatistik"],
        "question": "Haftalık su kullanım analizleri bana nasıl yardımcı olur?",
        "answer": """Hangi günlerde veya saatlerde fazla tüketim yaptığını net şekilde görmeni sağlar. 

Bu sayede alışkanlıklarını bilinçli olarak düzenleyebilirsin.

Veri gücü! Trendleri gör, aksiyon al. 📈"""
    },
    {
        "keywords": ["hedef koy", "amaç", "motivasyon", "goal"],
        "question": "Tasarruf hedefi koymak gerçekten işe yarar mı?",
        "answer": """Evet, kesinlikle işe yarıyor!

Net hedefler motivasyonu artırır ve tasarrufu sürdürülebilir hale getirir. 

Küçük ama ulaşılabilir hedefler en etkilisidir. Örneğin: 'Bu hafta %10 az su kullanacağım.' 🎯"""
    },
    {
        "keywords": ["normal mi", "fazla mı", "karşılaştır", "ortalama", "benchmark"],
        "question": "Su tüketimim normal mi yoksa fazla mı, bunu nasıl anlayabilirim?",
        "answer": """Benzer hane profilleriyle karşılaştırma yapmak ve geçmiş verilerine bakmak en doğru yöntemdir. 

Ortalama bir kişi günde 100-150 litre su kullanır.
4 kişilik bir aile için aylık ortalama: 12-15 m³

Böylece tüketiminin nerede durduğunu net görürsün. 📊"""
    },
    {
        "keywords": ["3 öneri", "bugün", "hemen", "şimdi", "pratik", "somut"],
        "question": "Bugünden itibaren su kullanımımı daha verimli hale getirmek için 3 net öneri verir misin?",
        "answer": """Tabii ki! İşte hemen uygulayabileceğin 3 öneri:

1️⃣ **Duş:** Süreyi kısalt ve sabunlanırken suyu kapat
2️⃣ **Makineler:** Çamaşır ve bulaşık makinelerini sadece tam doluyken çalıştır
3️⃣ **Akan su:** Akan su alışkanlıklarını bırak, kap içinde yıka

Bu 3 adım bile büyük fark yaratır! 💪"""
    }
]

def match_faq(user_message: str) -> str:
    """
    Match user message to FAQ database using keyword matching.
    Returns the answer if a match is found, otherwise returns None.
    """
    user_msg_lower = user_message.lower()
    
    best_match = None
    best_score = 0
    
    for faq in FAQ_DATABASE:
        score = 0
        for keyword in faq["keywords"]:
            if keyword in user_msg_lower:
                score += len(keyword)  # Longer keyword matches get higher score
        
        if score > best_score:
            best_score = score
            best_match = faq
    
    # Return answer if score is high enough (at least one keyword matched)
    if best_score > 0 and best_match:
        return best_match["answer"]
    
    return None

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def chat_with_ai(request: ChatRequest):
    """
    Advanced AI Chatbot - Natural language responses with contextual awareness.
    """
    import random
    from datetime import datetime
    
    user_message = request.message.lower().strip()
    current_hour = datetime.now().hour
    
    # Time-based greeting context
    if 5 <= current_hour < 12:
        time_greeting = "Günaydın"
        time_context = "sabah"
    elif 12 <= current_hour < 18:
        time_greeting = "İyi günler"
        time_context = "öğleden sonra"
    elif 18 <= current_hour < 22:
        time_greeting = "İyi akşamlar"
        time_context = "akşam"
    else:
        time_greeting = "İyi geceler"
        time_context = "gece"
    
    # Get current stats for context
    manual_entries = data_store.manual_entries
    budget = data_store.budget
    water_limit = data_store.monthly_water_limit
    
    # Get system simulation stats
    recent_data = data_store.get_simulation_window(hours=168)
    stats = CostCalculator.calculate_period_stats(
        recent_data, budget, data_store.reference_usage,
        manual_entries=manual_entries,
        session_system_usage=data_store.session_system_usage,
        session_system_cost=data_store.session_system_cost,
        session_hours=max(1, data_store.session_hours)
    )
    
    # Calculate detailed manual stats
    total_manual_usage = 0.0
    total_manual_cost = 0.0
    total_night_usage = 0.0
    daily_usages = []
    num_entries = len(manual_entries) if manual_entries else 0
    
    if manual_entries:
        sorted_dates = sorted(manual_entries.keys())
        for date_str in sorted_dates:
            data = manual_entries[date_str]
            if isinstance(data, dict):
                usage = float(data.get("total", 0))
                night = float(data.get("night", 0))
            else:
                usage = float(data)
                night = 0.0
            day_usage = usage - night
            cost = (day_usage * CostCalculator.UNIT_PRICE_DAY) + (night * CostCalculator.UNIT_PRICE_NIGHT)
            total_manual_usage += usage
            total_manual_cost += cost
            total_night_usage += night
            daily_usages.append(usage)
    
    daily_avg = total_manual_usage / num_entries if num_entries > 0 else 0
    monthly_projection = daily_avg * 30
    night_ratio = (total_night_usage / total_manual_usage * 100) if total_manual_usage > 0 else 0
    day_ratio = 100 - night_ratio
    
    # Trend analysis
    trend = "stable"
    trend_text = ""
    if len(daily_usages) >= 3:
        recent_avg = sum(daily_usages[-3:]) / 3
        older_avg = sum(daily_usages[:-3]) / max(1, len(daily_usages) - 3) if len(daily_usages) > 3 else recent_avg
        if recent_avg > older_avg * 1.1:
            trend = "increasing"
            trend_text = "Son günlerde kullanımınız artış eğiliminde"
        elif recent_avg < older_avg * 0.9:
            trend = "decreasing"
            trend_text = "Harika! Son günlerde kullanımınız düşüş eğiliminde"
        else:
            trend = "stable"
            trend_text = "Kullanımınız stabil seyrediyor"
    
    # Get optimization data
    opt = stats.get("optimization", {})
    opt_score = opt.get("score", 0)
    opt_status = opt.get("status", "Bilinmiyor")
    daily_water_target = opt.get("daily_water_target", 0)
    potential_savings = opt.get("potential_savings", 0)
    days_remaining = opt.get("days_remaining", 30)
    
    # Manual stats from metrics
    manual_proj_cost = stats.get("manual", {}).get("projection", 0)
    
    # Budget analysis
    budget_diff = budget - manual_proj_cost
    budget_status = "safe" if budget_diff > 0 else "risk"
    
    # Intelligent response generation
    response = ""
    
    # First, try to match FAQ database
    faq_answer = match_faq(user_message)
    if faq_answer:
        return {"response": faq_answer}
    
    # Greeting patterns
    if any(word in user_message for word in ["merhaba", "selam", "hey", "sa", "selamlar"]) and "nasıl" not in user_message:
        greetings = [
            f"{time_greeting}! 👋 Ben su tasarrufu asistanınızım. Bugün size nasıl yardımcı olabilirim?",
            f"{time_greeting}! 💧 Su kullanımınız, tasarruf fırsatları veya fatura analiziniz hakkında sorularınızı yanıtlamaya hazırım.",
            f"Hoş geldiniz! 🌊 {time_greeting.lower()}lar. Size özel su tasarrufu önerileri sunmak için buradayım. Ne merak ediyorsunuz?"
        ]
        response = random.choice(greetings)
        if num_entries > 0:
            response += f"\n\n💡 Bu arada, {num_entries} günlük veriniz var. 'Durumum nasıl?' diye sorarak detaylı analiz alabilirsiniz."
    
    # Status/Analysis queries
    elif any(word in user_message for word in ["durum", "özet", "nasıl gidiyor", "analiz", "nasıl", "nedir"]):
        if num_entries == 0:
            no_data_responses = [
                "Henüz analiz yapabilmem için veri yok. Ama endişelenmeyin, sol taraftaki formdan günlük su kullanımınızı girmeye başladığınızda size kapsamlı bir analiz sunacağım.",
                "Şu an için veriniz bulunmuyor. Günlük sayaç okumalarınızı girdiğinizde, kullanım trendlerinizi analiz edip kişiselleştirilmiş öneriler sunabileceğim.",
                "Veri girişi bekliyorum! 📝 Tarih, toplam kullanım ve gece kullanımını girerek başlayabilirsiniz. Ne kadar çok veri, o kadar isabetli analiz."
            ]
            response = random.choice(no_data_responses)
        else:
            # Comprehensive status analysis
            if opt_score >= 85:
                status_intro = f"🌟 Mükemmel bir performans sergiliyorsunuz! Optimizasyon skorunuz {opt_score:.0f}/100."
                status_mood = "harika"
            elif opt_score >= 70:
                status_intro = f"✅ Güzel gidiyorsunuz! Skorunuz {opt_score:.0f}/100, birkaç küçük iyileştirmeyle daha da yükselebilir."
                status_mood = "iyi"
            elif opt_score >= 50:
                status_intro = f"⚠️ Dikkat gerektiren noktalar var. Skorunuz {opt_score:.0f}/100, biraz odaklanmayla iyileştirebiliriz."
                status_mood = "orta"
            else:
                status_intro = f"🚨 Acil aksiyon gerekiyor! Skorunuz {opt_score:.0f}/100, ama birlikte çözeceğiz."
                status_mood = "kritik"
            
            # Find the peak usage day
            if daily_usages:
                max_usage = max(daily_usages)
                min_usage = min(daily_usages)
                max_day_idx = daily_usages.index(max_usage)
                max_day = list(sorted(manual_entries.keys()))[max_day_idx] if max_day_idx < len(manual_entries) else "bilinmiyor"
            else:
                max_usage = min_usage = 0
                max_day = "N/A"
            
            response = f"""{status_intro}

📊 **Kullanım Analizi ({num_entries} günlük veri)**

Günlük ortalamanız **{daily_avg:.0f}L** ve bu tempoda ay sonunda **{monthly_projection/1000:.2f}m³** kullanmış olacaksınız. {"Bu, belirlediğiniz limitin altında! 👍" if monthly_projection <= water_limit else f"Bu, {water_limit/1000:.1f}m³ limitinizi aşıyor! ⚠️"}

{trend_text + "." if trend_text else ""}

📈 **Detaylı İstatistikler:**
• En yüksek kullanım: {max_usage:.0f}L ({max_day})
• En düşük kullanım: {min_usage:.0f}L
• Gece/Gündüz oranı: %{night_ratio:.0f} gece, %{day_ratio:.0f} gündüz

💰 **Finansal Özet:**
Şu ana kadar {total_manual_cost:.2f}₺ harcadınız. Aylık projeksiyon: {manual_proj_cost:.2f}₺
{"✅ Bütçenizin " + f"{budget_diff:.2f}₺ altındasınız." if budget_status == "safe" else "⚠️ Bütçeyi " + f"{abs(budget_diff):.2f}₺ aşma riskiniz var!"}

🎯 **Günlük Hedef:** {daily_water_target:.0f}L {"- Hedefin altındasınız, süper!" if daily_avg <= daily_water_target else "- Biraz kısmamız gerekiyor."}"""

    # Savings/Tips queries
    elif any(word in user_message for word in ["tasarruf", "azalt", "düşür", "öneri", "ipucu", "nasıl kısa", "ne yapmalı", "yardım"]):
        tips = []
        priority_tips = []
        
        # Priority issues first
        if night_ratio > 35:
            priority_tips.append(f"🔴 **Öncelikli Konu - Gece Kullanımı**\nGece oranınız %{night_ratio:.0f} ve bu çok yüksek. Gece tarifesi gündüzün 2 katı! Bu kullanımı gündüze kaydırmanız ayda yaklaşık **{potential_savings:.0f}₺** tasarruf sağlar. Çamaşır ve bulaşık makinelerini 22:00'dan önce çalıştırmayı deneyin.")
        
        if daily_avg > daily_water_target * 1.2 and daily_water_target > 0:
            excess = daily_avg - daily_water_target
            priority_tips.append(f"🔴 **Öncelikli Konu - Günlük Aşım**\nGünlük hedefiniz {daily_water_target:.0f}L ama ortalamanız {daily_avg:.0f}L. Günde **{excess:.0f}L** fazla kullanıyorsunuz. Bu ay sonunda ciddi farka dönüşür.")
        
        if trend == "increasing":
            priority_tips.append("🔴 **Trend Uyarısı**\nSon günlerde kullanımınız artış eğiliminde. Bu trendi tersine çevirmek için hemen aksiyon alalım.")
        
        # Contextual tips
        if 6 <= current_hour <= 9:
            tips.append("☀️ **Sabah Rutini İpucu:** Sabah duşunu 1 dakika kısaltmak bile ayda 150L tasarruf demek. Bugün bunu deneyin!")
        elif 18 <= current_hour <= 21:
            tips.append("🌆 **Akşam İpucu:** Akşam yemeği bulaşıklarını makineye doldurun ama 22:00'dan önce çalıştırın, gece tarifesine yakalanmayın!")
        elif current_hour >= 22 or current_hour < 4:
            tips.append("🌙 **Gece Uyarısı:** Şu an gece tarifesi aktif! Makine çalıştırmayın, sabahı bekleyin.")
        
        tips.append("💧 **Duş:** Her duşta sabunlanırken musluğu kapatmak yılda 10.000L+ tasarruf sağlar.")
        tips.append("🍽️ **Bulaşık:** Makineyi yarım çalıştırmak tam çalıştırmakla aynı suyu harcar. Sabırlı olun, dolmasını bekleyin.")
        tips.append("🧺 **Çamaşır:** Haftada 1 yıkama azaltmak yılda 2.500L+ tasarruf demek.")
        tips.append("🔧 **Bakım:** Akan musluk günde 20L, yılda 7.300L kayıp. Contaları kontrol edin.")
        
        if priority_tips:
            response = "⚡ **Sizin İçin Öncelikli Konular:**\n\n" + "\n\n".join(priority_tips)
            response += "\n\n---\n\n💡 **Genel Öneriler:**\n\n" + "\n\n".join(tips[:3])
        else:
            intro_phrases = [
                "Verilerinize baktım, işte size özel önerilerim:",
                "Kullanım paternlerinizi analiz ettim. Şunları öneriyorum:",
                "Fatura tasarrufu için yapabilecekleriniz:"
            ]
            response = random.choice(intro_phrases) + "\n\n" + "\n\n".join(tips[:5])

    # Cost/Bill queries  
    elif any(word in user_message for word in ["fatura", "maliyet", "para", "ücret", "ne kadar", "tutar", "hesap"]):
        if num_entries == 0:
            response = """💰 **Fatura Analizi İçin Veri Gerekli**

Henüz su kullanım veriniz yok. Doğru bir fatura tahmini yapabilmem için:

1️⃣ Sol panelden tarih seçin
2️⃣ O günkü toplam kullanımı (litre) girin
3️⃣ Gece kullanımını (22:00-04:00) belirtin

En az 3-5 günlük veri girdiğinizde size güvenilir bir aylık projeksiyon sunabilirim. Sayaç okumanız yoksa, ortalama bir hane günde 150-200L kullanır diye tahmin yapabiliriz.

Başlamak ister misiniz?"""
        else:
            daily_cost_avg = total_manual_cost / num_entries
            night_extra_cost = total_night_usage * CostCalculator.UNIT_PRICE_DAY
            
            # Calculate what they'd pay with optimal usage
            optimal_cost = daily_water_target * 30 * CostCalculator.UNIT_PRICE_DAY
            
            response = f"""💰 **Detaylı Fatura Raporu**

📊 **{num_entries} Günlük Harcama Analizi:**
• Toplam harcama: **{total_manual_cost:.2f}₺**
• Günlük ortalama: **{daily_cost_avg:.2f}₺**
• Bu ay için projeksiyon: **{manual_proj_cost:.2f}₺**

💵 **Bütçe Karşılaştırması:**
• Belirlenen bütçe: {budget:.2f}₺
• Projeksiyon: {manual_proj_cost:.2f}₺
• Fark: {"+" if budget_diff > 0 else ""}{budget_diff:.2f}₺ {"✅" if budget_diff > 0 else "⚠️"}

{"🎉 Harika! Bütçenizin altındasınız, bu tempoyu koruyun!" if budget_diff > 0 else "📉 Dikkat! Bu gidişle bütçeyi aşacaksınız. Tasarruf önerilerime göz atın."}

💡 **Tasarruf Fırsatları:**
• Gece kullanımını optimize ederek: ~{night_extra_cost:.2f}₺/ay kazanabilirsiniz
• Optimal kullanımla aylık faturanız: ~{optimal_cost:.2f}₺ olabilir

Detaylı tasarruf planı için "tasarruf önerileri" yazabilirsiniz."""

    # Night tariff queries
    elif any(word in user_message for word in ["gece", "tarife", "saat", "pahalı", "ucuz"]):
        is_night_now = current_hour >= 22 or current_hour < 4
        
        response = f"""🌙 **Gece Tarifesi Rehberi**

⏰ **Tarife Saatleri:**
• 🌞 Gündüz (04:00-22:00): Normal tarife ({CostCalculator.UNIT_PRICE_DAY:.4f}₺/L)
• 🌙 Gece (22:00-04:00): **2x pahalı** ({CostCalculator.UNIT_PRICE_NIGHT:.4f}₺/L)

{"🔴 **ŞU AN GECE TARİFESİ AKTİF!** Makine çalıştırmayın, sabah 04:00'ı bekleyin." if is_night_now else "🟢 Şu an gündüz tarifesi aktif. Makinelerinizi çalıştırmak için uygun zaman!"}

📊 **Sizin Gece Kullanımınız:**
• Gece oranı: **%{night_ratio:.0f}** ({total_night_usage:.0f}L)
• Değerlendirme: {"✅ İdeal seviyede!" if night_ratio < 20 else "⚠️ Biraz yüksek, iyileştirme şansı var!" if night_ratio < 35 else "🔴 Çok yüksek! Acil aksiyon alın."}

💡 **Pratik Öneriler:**
• Çamaşır makinesi: 21:00'da değil, 20:00'da başlatın
• Bulaşık makinesi: Akşam yemeğinden sonra hemen çalıştırın
• Duş: Gece geç saatlerden kaçının

Gece kullanımınızı gündüze kaydırarak ayda **{(total_night_usage * CostCalculator.UNIT_PRICE_DAY):.2f}₺** tasarruf edebilirsiniz!"""

    # Budget/Goal queries
    elif any(word in user_message for word in ["limit", "hedef", "bütçe", "amaç", "goal"]):
        progress_usage = (total_manual_usage / water_limit * 100) if water_limit > 0 else 0
        progress_cost = (total_manual_cost / budget * 100) if budget > 0 else 0
        
        # Progress bar visualization
        def make_progress_bar(pct):
            filled = int(pct / 10)
            empty = 10 - filled
            return "█" * min(filled, 10) + "░" * max(empty, 0)
        
        response = f"""🎯 **Hedef Takip Paneli**

💧 **Su Kullanım Hedefi:**
{make_progress_bar(progress_usage)} {progress_usage:.0f}%
• Limit: {water_limit:.0f}L ({water_limit/1000:.1f}m³)
• Kullanılan: {total_manual_usage:.0f}L
• Kalan: {max(0, water_limit - total_manual_usage):.0f}L
{"✅ Hedef dahilinde!" if progress_usage <= 100 else "⚠️ Limit aşıldı!"}

💰 **Bütçe Hedefi:**
{make_progress_bar(progress_cost)} {progress_cost:.0f}%
• Bütçe: {budget:.2f}₺
• Harcanan: {total_manual_cost:.2f}₺
• Kalan: {max(0, budget - total_manual_cost):.2f}₺
{"✅ Bütçe dahilinde!" if progress_cost <= 100 else "⚠️ Bütçe aşıldı!"}

📅 **Günlük Hedefler:**
• Su: {daily_water_target:.0f}L/gün
• Bütçe: {budget/30:.2f}₺/gün
• Mevcut ortalamanız: {daily_avg:.0f}L/gün

Hedeflerinizi güncellemek için sol panelden yeni bütçe girebilirsiniz. Sistem otomatik olarak su limitinizi hesaplayacaktır."""

    # Laundry queries
    elif any(word in user_message for word in ["çamaşır", "yıkama", "deterjan", "çamaşır tasarrufu", "çamaşır ipucu"]):
        response = f"""🧺 **Akıllı Çamaşır Yıkama Rehberi**

💧 **Su Tüketim Tablosu:**
| Program | Su (L) | Maliyet |
|---------|--------|---------|
| Normal | 50-60L | ~{55*CostCalculator.UNIT_PRICE_DAY:.2f}₺ |
| Eko | 40-50L | ~{45*CostCalculator.UNIT_PRICE_DAY:.2f}₺ |
| Hızlı | 40-45L | ~{42*CostCalculator.UNIT_PRICE_DAY:.2f}₺ |

⚠️ **Kritik Bilgi:** Yarım yük = tam yük aynı su! Her zaman tam doldurun.

💡 **Sizin İçin Öneriler:**
{"• Gece çamaşır yıkıyorsunuz gibi görünüyor. Gündüze kaydırarak tasarruf edin!" if night_ratio > 30 else "• Gündüz yıkama alışkanlığınız iyi, devam edin!"}
• Haftada 1 yıkama azaltmak = yılda **2.500L** ve **~{2500*CostCalculator.UNIT_PRICE_DAY:.0f}₺** tasarruf
• Eko programı tercih edin - daha uzun ama daha ekonomik

📊 **Hesaplama:**
Haftada 3 yıkama yapıyorsanız: Ayda ~{3*4*50:.0f}L ve ~{3*4*50*CostCalculator.UNIT_PRICE_DAY:.2f}₺
1 yıkama azaltırsanız: Ayda ~{2*4*50:.0f}L ve ~{2*4*50*CostCalculator.UNIT_PRICE_DAY:.2f}₺"""

    # Shower/Bath queries
    elif any(word in user_message for word in ["duş", "banyo", "yıkan", "duş ipuçları", "duş ipucu", "duş tasarrufu"]):
        response = f"""🚿 **Akıllı Duş ve Banyo Rehberi**

💧 **Su Tüketim Karşılaştırması:**
| Aktivite | Su (L) | Maliyet |
|----------|--------|---------|
| 5 dk duş | ~40L | ~{40*CostCalculator.UNIT_PRICE_DAY:.2f}₺ |
| 10 dk duş | ~80L | ~{80*CostCalculator.UNIT_PRICE_DAY:.2f}₺ |
| 15 dk duş | ~120L | ~{120*CostCalculator.UNIT_PRICE_DAY:.2f}₺ |
| Küvet | 150-200L | ~{175*CostCalculator.UNIT_PRICE_DAY:.2f}₺ |

⏱️ **Dakika Başına Etki:**
Her ekstra dakika = ~8L ekstra su = ~{8*CostCalculator.UNIT_PRICE_DAY:.3f}₺

💡 **Pratik Tasarruf Taktikleri:**
1. **Sabunlanırken kapat:** Her duşta 20-30L tasarruf
2. **Zamanlayıcı kur:** Telefon alarmı ile duş süresini kontrol et
3. **Tasarruflu başlık:** %30-50 daha az su, aynı basınç hissi
4. **Küvetten kaçın:** 1 küvet = 2-3 duş

{"⚠️ Gece duş alıyorsanız, 22:00'dan önce almaya çalışın!" if night_ratio > 20 else ""}

📊 **Aylık Etki Hesabı:**
Günde 2 dk kısaltma × 30 gün = **600L** ve **{600*CostCalculator.UNIT_PRICE_DAY:.2f}₺** tasarruf!"""

    # Dishwasher queries
    elif any(word in user_message for word in ["bulaşık", "tabak", "bardak", "bulaşık tasarrufu", "bulaşık ipucu"]):
        response = f"""🍽️ **Akıllı Bulaşık Yıkama Rehberi**

💧 **Yöntem Karşılaştırması:**
| Yöntem | Su (L) | Maliyet | Verimlilik |
|--------|--------|---------|------------|
| Akan su (elde) | 30-40L | ~{35*CostCalculator.UNIT_PRICE_DAY:.2f}₺ | ❌ Düşük |
| Leğende (elde) | 10-15L | ~{12*CostCalculator.UNIT_PRICE_DAY:.2f}₺ | ✅ İyi |
| Makine (tam) | 12-15L | ~{13*CostCalculator.UNIT_PRICE_DAY:.2f}₺ | ✅✅ En iyi |
| Makine (yarım) | 12-15L | ~{13*CostCalculator.UNIT_PRICE_DAY:.2f}₺ | ❌ İsraf |

⚠️ **Kritik:** Makine yarım da çalışsa tam da, aynı suyu kullanır!

💡 **Altın Kurallar:**
1. **Ön durulama yapmayın** - Kazıyın, direkt makineye
2. **Tam dolmasını bekleyin** - Sabırlı olun
3. **Eko programı seçin** - Daha uzun ama daha ekonomik
4. **Gündüz çalıştırın** - 22:00 öncesi {"⚠️ Şu an gece tarifesi!" if (current_hour >= 22 or current_hour < 4) else "✅ Şu an uygun zaman!"}

📊 **Tasarruf Potansiyeli:**
Elden makineye geçiş = ayda **~500L** ve **{500*CostCalculator.UNIT_PRICE_DAY:.2f}₺** tasarruf"""

    # Thanks responses
    elif any(word in user_message for word in ["teşekkür", "sağol", "eyvallah", "tşk", "ty", "thanks"]):
        thanks_responses = [
            "Rica ederim! 😊 Başka bir konuda yardımcı olabilir miyim?",
            "Ne demek, her zaman buradayım! 💧 Başka sorunuz varsa çekinmeyin.",
            "Memnuniyetle! Su tasarrufu yolculuğunuzda yanınızdayım. 🌊",
            f"Rica ederim! Mevcut skorunuz {opt_score:.0f}/100. Daha da iyileştirebiliriz! 🎯"
        ]
        response = random.choice(thanks_responses)

    # Who are you queries
    elif any(word in user_message for word in ["kimsin", "nesin", "adın", "hakkında", "tanı"]):
        response = f"""🤖 **Hakkımda**

Ben su tasarrufu konusunda uzmanlaşmış bir yapay zeka asistanıyım. Amacım, su kullanımınızı analiz ederek hem bütçenizi hem de çevreyi korumanıza yardımcı olmak.

**Yapabileceklerim:**
• 📊 Kullanım verilerinizi analiz edip trendleri tespit etmek
• 💡 Kişiselleştirilmiş tasarruf önerileri sunmak
• 💰 Fatura projeksiyonları hesaplamak
• 🎯 Hedef takibi yapmak
• ⏰ Gece/gündüz tarife optimizasyonu önermek

**Bilmem Gerekenler:**
Günlük su kullanımınızı girdiğinizde size daha isabetli öneriler sunabilirim. Şu an {num_entries} günlük veriniz var.

Size nasıl yardımcı olabilirim?"""

    # Default/Help response
    else:
        help_phrases = [
            f"Hmm, tam olarak ne sorduğunuzu anlayamadım. Ama yardımcı olmak istiyorum!",
            f"Bu konuda kesin bir cevabım yok, ama su tasarrufu konusunda uzmanım.",
            f"Sorunuzu farklı şekilde sormayı dener misiniz?"
        ]
        
        response = f"""{random.choice(help_phrases)}

🔍 **Size yardımcı olabileceğim konular:**

📊 **"Durumum nasıl?"**
→ Detaylı kullanım analizi, trend takibi, optimizasyon skoru

💡 **"Tasarruf önerileri"**
→ Verilerinize göre kişiselleştirilmiş ipuçları

💰 **"Fatura tahmini"**
→ Aylık maliyet projeksiyonu ve bütçe karşılaştırması

🌙 **"Gece tarifesi"**
→ Tarife saatleri ve optimizasyon fırsatları

🎯 **"Hedeflerim"**
→ İlerleme takibi ve hedef durumu

🚿 **"Duş/Çamaşır/Bulaşık"**
→ Detaylı tasarruf rehberleri

---
💡 Mevcut skorunuz: **{opt_score:.0f}/100** ({opt_status})
{f"📈 Trend: {trend_text}" if trend_text else ""}"""
    
    return {"response": response}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
