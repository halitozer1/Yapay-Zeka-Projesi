import React, { useEffect, useState, useRef } from 'react';
import './theme.css';
import { RealTimeGraph } from './components/RealTimeGraph';
import { ReportModal } from './components/ReportModal';
import { BudgetPanel } from './components/BudgetPanel';
import { OptimizationActions } from './components/OptimizationActions';
import { StrategyCard } from './components/StrategyCard';
import { Chatbot } from './components/Chatbot';
import { api } from './api';
import { Droplets, Lightbulb } from 'lucide-react';

function App() {
  const [metrics, setMetrics] = useState(null);
  const [manualDate, setManualDate] = useState('');
  const [manualAmount, setManualAmount] = useState('');
  const [manualNightAmount, setManualNightAmount] = useState('');
  const [isAdding, setIsAdding] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [reportSnapshot, setReportSnapshot] = useState([]);
  const [frozenRecommendations, setFrozenRecommendations] = useState([]);
  const [manualBudgetInput, setManualBudgetInput] = useState('');
  const [manualWaterInput, setManualWaterInput] = useState('');
  const [isPaused, setIsPaused] = useState(false);
  const hasInitialized = useRef(false);

  const fetchMetrics = async () => {
    try {
      const data = await api.getMetrics();
      setMetrics(data);

      // Only initialize frozen recommendations ONCE, and NOT from the repeating interval closure
      if (!hasInitialized.current && data.recommendations && data.recommendations.length > 0) {
        setFrozenRecommendations(data.recommendations);
        hasInitialized.current = true;
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleManualAdd = async () => {
    if (!manualDate || !manualAmount) return;
    setIsAdding(true);
    try {
      await api.addManualEntry(
        manualDate,
        parseFloat(manualAmount),
        parseFloat(manualNightAmount || 0)
      );
      setManualDate('');
      setManualAmount('');
      setManualNightAmount('');
      fetchMetrics();
      alert('Veri başarıyla eklendi!');
    } catch (e) {
      console.error("Manual add failed:", e);
      alert('Hata: Veri eklenemedi.');
    } finally {
      setIsAdding(false);
    }
  };

  const handleManualDelete = async (date) => {
    if (!window.confirm(`${date} tarihli veriyi silmek istediğinize emin misiniz?`)) return;
    try {
      await api.deleteManualEntry(date);
      fetchMetrics();
    } catch (e) {
      console.error("Delete failed:", e);
      alert("Hata: Kayıt silinemedi.");
    }
  };

  const handleSetWaterLimit = async (amount) => {
    try {
      await api.setWaterLimit(amount);
      fetchMetrics();
    } catch (e) {
      console.error("Water limit update failed:", e);
    }
  };

  const handleSetBudget = async (amount) => {
    try {
      await api.setBudget(amount);
      fetchMetrics();
    } catch (e) {
      console.error("Budget update failed:", e);
    }
  };

  const handleSkipSimulation = async () => {
    try {
      const resp = await api.skipSimulation();

      const data = await api.getMetrics();
      setMetrics(data);
      setReportSnapshot(data.recommendations || []);
      setFrozenRecommendations(data.recommendations || []);
      setIsModalOpen(true);

      if (resp.period_completed) {
        setIsPaused(true);
      }
    } catch (e) {
      console.error("Skip failed:", e);
    }
  };

  const handleResumeSimulation = async () => {
    try {
      await api.resumeSimulation();
      setIsPaused(false);
      fetchMetrics();
    } catch (e) {
      console.error("Resume failed:", e);
    }
  };

  useEffect(() => {
    fetchMetrics();
    fetchMetrics();
    const interval = setInterval(() => {
      if (!isPaused) fetchMetrics();
    }, 1500); // 1.5 sn'de bir yenile
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1 style={{ display: 'flex', alignItems: 'center', gap: '1rem', fontSize: '2rem', fontWeight: '800', background: 'linear-gradient(to right, #3b82f6, #06b6d4)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', margin: 0 }}>
          <Droplets size={40} color="#3b82f6" />
          Su Optimizasyon Asistanı
        </h1>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>SİSTEM DURUMU</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#10b981', fontWeight: 'bold' }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981' }} />
              Aktif Analiz
            </div>
          </div>
          <button
            onClick={() => {
              const recs = metrics?.recommendations || [];
              setReportSnapshot(recs); // Freeze for modal
              setFrozenRecommendations(recs); // Freeze for sidebar too
              setIsModalOpen(true);
            }}
            style={{ padding: '0.5rem 1rem', background: '#1e293b', border: '1px solid #334155', borderRadius: 'var(--radius)', color: 'white', cursor: 'pointer', fontSize: '0.875rem', fontWeight: 'bold' }}
          >
            Aylık Karne
          </button>
        </div>
      </header>

      {/* Monthly Report Modal */}
      <ReportModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        recommendations={reportSnapshot}
      />

      <main style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '2rem' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          <StrategyCard metrics={metrics} />

          <RealTimeGraph
            onSkip={handleSkipSimulation}
            onResume={handleResumeSimulation}
            isPaused={isPaused}
          />

          {/* Manual Entry Section */}
          <div style={{ backgroundColor: 'var(--color-surface)', padding: '1.5rem', borderRadius: 'var(--radius)' }}>
            <h3>Günlük Manuel Veri Girişi</h3>
            <p style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>Faturanızdaki günlük kullanımı ve gece (22:00-04:00) kullanımını ekleyin.</p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr auto', gap: '0.75rem' }}>
              <input
                type="date"
                value={manualDate}
                onChange={(e) => setManualDate(e.target.value)}
                style={{ padding: '0.5rem', borderRadius: 'var(--radius)', border: '1px solid #334155', background: '#0f172a', color: 'white', width: '100%' }}
              />
              <input
                type="number"
                placeholder="Toplam (L)"
                value={manualAmount}
                onChange={(e) => setManualAmount(e.target.value)}
                style={{ padding: '0.5rem', borderRadius: 'var(--radius)', border: '1px solid #334155', background: '#0f172a', color: 'white', width: '100%' }}
              />
              <input
                type="number"
                placeholder="Gece (L)"
                value={manualNightAmount}
                onChange={(e) => setManualNightAmount(e.target.value)}
                style={{ padding: '0.5rem', borderRadius: 'var(--radius)', border: '1px solid #334155', background: '#0f172a', color: 'white', width: '100%' }}
              />
              <button
                onClick={handleManualAdd}
                disabled={isAdding}
                style={{ padding: '0.5rem 1.5rem', background: 'var(--color-primary)', border: 'none', borderRadius: 'var(--radius)', color: 'white', cursor: 'pointer', fontWeight: 'bold' }}
              >
                {isAdding ? '...' : 'Ekle'}
              </button>
            </div>

            {/* Unified Master Control: Budget auto-updates Water Limit */}
            <div style={{
              marginTop: '1.5rem',
              padding: '1.2rem',
              background: 'rgba(59, 130, 246, 0.08)',
              borderRadius: 'var(--radius)',
              border: '1px solid rgba(59, 130, 246, 0.2)',
            }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 'bold', color: 'var(--color-primary)', display: 'block', marginBottom: '0.6rem' }}>
                GENEL AYAR: AYLIK HEDEF BÜTÇE (₺)
                {metrics?.monthly_water_limit && (
                  <span style={{ fontWeight: 'bold', color: '#10b981', fontSize: '0.85rem', marginLeft: '0.5rem' }}>
                    → {metrics.monthly_water_limit.toLocaleString('tr-TR', { maximumFractionDigits: 0 })} L SU HAKKINIZ VAR
                  </span>
                )}
              </label>
              <div style={{ display: 'flex', gap: '0.8rem' }}>
                <input
                  type="number"
                  placeholder={metrics?.budget?.toString() || "Bütçe Girin (₺)"}
                  value={manualBudgetInput}
                  onChange={(e) => setManualBudgetInput(e.target.value)}
                  style={{ flex: 1, padding: '0.5rem', borderRadius: '4px', border: '1px solid #334155', background: '#0f172a', color: 'white', fontSize: '1rem' }}
                />
                <button
                  onClick={() => {
                    if (manualBudgetInput) {
                      handleSetBudget(parseFloat(manualBudgetInput));
                      setManualBudgetInput('');
                    }
                  }}
                  style={{ padding: '0.5rem 1.5rem', background: 'var(--color-primary)', border: 'none', borderRadius: '4px', color: 'white', cursor: 'pointer', fontSize: '0.9rem', fontWeight: 'bold' }}
                >
                  Bütçeyi Kaydet
                </button>
              </div>
              <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.75rem', color: 'var(--color-text-muted)', fontStyle: 'italic' }}>
                *Sistem, belirlediğiniz bütçeye göre otomatik olarak su limitinizi ("param kadar su") güncelleyecektir.
              </p>
            </div>

          </div>

          {/* Manual Analysis & Summary Section */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {/* Manual Entries Summary */}
            <div style={{ backgroundColor: 'var(--color-surface)', padding: '1.5rem', borderRadius: 'var(--radius)' }}>
              <h3 style={{ marginBottom: '1rem', borderBottom: '1px solid #334155', paddingBottom: '0.5rem' }}>Giriş Özeti</h3>
              <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                {!metrics?.manual_entries || Object.keys(metrics.manual_entries).length === 0 ? (
                  <p style={{ color: 'var(--color-text-muted)' }}>Henüz manuel veri girişi yapılmadı.</p>
                ) : (
                  <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
                        <th style={{ paddingBottom: '0.5rem' }}>Tarih</th>
                        <th style={{ paddingBottom: '0.5rem', textAlign: 'right' }}>Toplam (L)</th>
                        <th style={{ paddingBottom: '0.5rem', textAlign: 'right' }}>Gece (L)</th>
                        <th style={{ paddingBottom: '0.5rem', textAlign: 'right' }}>İşlem</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(metrics.manual_entries)
                        .sort((a, b) => b[0].localeCompare(a[0]))
                        .map(([date, data]) => {
                          const total = typeof data === 'object' ? data.total : data;
                          const night = typeof data === 'object' ? data.night : 0;
                          return (
                            <tr key={date} style={{ borderBottom: '1px solid #1e293b' }}>
                              <td style={{ padding: '0.75rem 0' }}>{date}</td>
                              <td style={{ padding: '0.75rem 0', textAlign: 'right', fontWeight: 'bold', color: '#f97316' }}>{total.toFixed(0)} L</td>
                              <td style={{ padding: '0.75rem 0', textAlign: 'right', color: '#94a3b8' }}>{night.toFixed(0)} L</td>
                              <td style={{ padding: '0.75rem 0', textAlign: 'right' }}>
                                <button
                                  onClick={() => handleManualDelete(date)}
                                  style={{ background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', border: 'none', padding: '0.2rem 0.5rem', borderRadius: '0.25rem', cursor: 'pointer', fontSize: '0.75rem' }}
                                > Sil </button>
                              </td>
                            </tr>
                          );
                        })}
                    </tbody>
                  </table>
                )}
              </div>
            </div>

            {/* Manual AI Recommendations Card */}
            <div style={{
              backgroundColor: 'var(--color-surface)',
              padding: '1.5rem',
              borderRadius: 'var(--radius)',
              borderLeft: '4px solid #f97316'
            }}>
              <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: 0, color: '#f97316', fontSize: '1.17rem', fontWeight: 'bold' }}>
                <Lightbulb size={20} />
                Yapay Zeka Önerileri (Manuel)
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '1rem' }}>
                {metrics?.manual_recommendations ? metrics.manual_recommendations.map((rec, i) => (
                  <div key={i} style={{
                    fontSize: '0.95rem',
                    lineHeight: '1.5',
                    color: rec.startsWith('•') ? '#f97316' : 'var(--color-text)',
                    paddingLeft: rec.startsWith('•') ? '1rem' : '0',
                    fontWeight: rec.includes('Merhaba') || rec.includes('Böylelikle') || rec.includes('İnceledim') ? 'bold' : 'normal'
                  }}>
                    {rec}
                  </div>
                )) : (
                  <div style={{ color: 'var(--color-text-muted)' }}>Manuel analiz için veri bekleniyor...</div>
                )}
              </div>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          <BudgetPanel metrics={metrics} onUpdate={fetchMetrics} />
          <OptimizationActions metrics={metrics} frozenRecommendations={frozenRecommendations} />
        </div>
      </main>
      <Chatbot />
    </div>
  );
}

export default App;
