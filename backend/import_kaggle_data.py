import pandas as pd
import os
import glob
from datetime import datetime

def find_new_csv():
    # usage_real.csv haricindeki csv dosyalarına bak
    files = glob.glob("*.csv")
    candidates = [f for f in files if "usage_real.csv" not in f]
    return candidates[0] if candidates else None

def normalize_and_import(file_path):
    print(f"Işleniyor: {file_path}...")
    
    try:
        df = pd.read_csv(file_path)
        print(f"Sütunlar: {list(df.columns)}")
        
        # Kaggle datasetlerinde genelde Date ve Time ayrı olabilir veya tek Timestamp olabilir.
        # Otomatik algılama denemesi:
        
        # 1. Tarih/Saat sütunu belirleme
        date_col = None
        time_col = None
        usage_col = None
        
        # Olası sütun isimleri
        date_candidates = ['Date', 'date', 'Day', 'day', 'Timestamp', 'timestamp', 'DT']
        time_candidates = ['Time', 'time', 'Hour', 'hour']
        usage_candidates = ['Usage', 'usage', 'Consumption', 'consumption', 'Volume', 'volume', 'Liters', 'liters', 'Water', 'water']

        for col in df.columns:
            if col in date_candidates:
                date_col = col
            elif col in time_candidates:
                time_col = col
            elif any(c in col for c in usage_candidates):
                usage_col = col

        # Eğer sütunlar bulunamadıysa manuel mapping (Kaggle Pince7489 dataset tahmini)
        if not date_col:
            # Genelde ddate, Date vb.
            date_col = df.columns[0] # İlk sütunu tarih varsay
        if not usage_col:
            usage_col = df.columns[-1] # Son sütunu kullanım varsay

        print(f"Mapping -> Tarih: {date_col}, Saat: {time_col}, Kullanım: {usage_col}")

        # Tarih ve Saati birleştir
        if time_col:
            df['timestamp'] = pd.to_datetime(df[date_col].astype(str) + ' ' + df[time_col].astype(str))
        else:
            df['timestamp'] = pd.to_datetime(df[date_col])

        # Kullanım verisini sayıya çevir
        df['usage_liters'] = pd.to_numeric(df[usage_col], errors='coerce').fillna(0)

        # Sadece gereken sütunları al
        final_df = df[['timestamp', 'usage_liters']].copy()
        
        # Tarihe göre sırala
        final_df = final_df.sort_values('timestamp')
        
        # Saatlik değilse veya eksik varsa düzeltme (Resample to Hourly)
        final_df.set_index('timestamp', inplace=True)
        # Saatlik toplama (veya ortalama)
        resampled_df = final_df.resample('h').sum().fillna(0)
        resampled_df.reset_index(inplace=True)

        # Kaydet
        output_path = "usage_real.csv"
        resampled_df.to_csv(output_path, index=False)
        print(f"✅ Başarıyla dönüştürüldü ve '{output_path}' dosyasına kaydedildi!")
        print(f"Toplam {len(resampled_df)} saatlik veri oluşturuldu.")
        
    except Exception as e:
        print(f"❌ Hata oluştu: {e}")

if __name__ == "__main__":
    csv_file = find_new_csv()
    if csv_file:
        normalize_and_import(csv_file)
    else:
        print("⚠️ Klasörde 'usage_real.csv' dışında bir CSV dosyası bulunamadı.")
        print("Lütfen indirdiğiniz dosyayı backend klasörüne atın.")
