import React from 'react';
import { Target, TrendingUp, AlertCircle, Clock } from 'lucide-react';

export const StrategyCard = ({ metrics }) => {
    if (!metrics || !metrics.stats || !metrics.stats.optimization) return null;

    const opt = metrics.stats.optimization;

    // Status color mapping
    const getStatusColor = (status) => {
        if (status.includes("Mükemmel")) return "#10b981";
        if (status.includes("Dengeli")) return "#3b82f6";
        if (status.includes("Dikkatli")) return "#f59e0b";
        return "#ef4444";
    };

    const statusColor = getStatusColor(opt.status);

    return (
        <div style={{
            backgroundColor: 'var(--color-surface)',
            padding: '1.5rem',
            borderRadius: 'var(--radius)',
            border: `1px solid ${statusColor}44`,
            position: 'relative',
            overflow: 'hidden'
        }}>
            {/* Status Indicator Background */}
            <div style={{
                position: 'absolute',
                top: 0,
                right: 0,
                width: '100px',
                height: '100px',
                background: `radial-gradient(circle at top right, ${statusColor}22, transparent)`,
                zIndex: 0
            }} />

            <div style={{ position: 'relative', zIndex: 1 }}>
                <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                    <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', margin: 0, fontSize: '1.25rem' }}>
                        <Target size={24} color={statusColor} />
                        Optimizasyon Stratejisi
                    </h2>
                    <div style={{
                        background: `${statusColor}22`,
                        color: statusColor,
                        padding: '0.25rem 0.75rem',
                        borderRadius: '1rem',
                        fontSize: '0.875rem',
                        fontWeight: 'bold',
                        border: `1px solid ${statusColor}44`
                    }}>
                        {opt.status}
                    </div>
                </header>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                    {/* Daily Target Section */}
                    <div style={{ background: 'rgba(30, 41, 59, 0.3)', padding: '1rem', borderRadius: '0.5rem' }}>
                        <div style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                            <Clock size={14} /> BUGÜN İÇİN İDEAL HEDEF
                        </div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#f8fafc' }}>
                            {opt.daily_water_target} <span style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>Litre</span>
                        </div>
                        <div style={{ fontSize: '0.75rem', color: `${statusColor}cc`, marginTop: '0.25rem' }}>
                            Kalan {opt.days_remaining} gün için önerilen limit.
                        </div>
                    </div>

                    {/* Savings Potential Section */}
                    <div style={{ background: 'rgba(30, 41, 59, 0.3)', padding: '1rem', borderRadius: '0.5rem' }}>
                        <div style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                            <TrendingUp size={14} /> TARİFE TASARRUF POTANSİYELİ
                        </div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#10b981' }}>
                            {opt.potential_savings.toFixed(2)} ₺
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: '0.25rem' }}>
                            Gece kullanımını gündüze kaydırarak kazanabilirsiniz.
                        </div>
                    </div>
                </div>

                <div style={{ marginTop: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.8rem', padding: '0.75rem', background: 'rgba(59, 130, 246, 0.05)', borderRadius: '0.5rem', border: '1px solid rgba(59, 130, 246, 0.1)' }}>
                    <AlertCircle size={20} color="var(--color-primary)" />
                    <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
                        <strong style={{ color: 'var(--color-text)' }}>Optimizasyon Skoru: {opt.score}%</strong> - {opt.score > 80 ? 'Harika bir yoldasınız!' : 'Maliyetleri düşürmek için önerilere göz atın.'}
                    </p>
                </div>
            </div>
        </div>
    );
};
