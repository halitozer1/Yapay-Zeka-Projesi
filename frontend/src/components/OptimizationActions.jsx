import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { Lightbulb, Leaf, Droplets, Cloud } from 'lucide-react';

export const OptimizationActions = ({ metrics, frozenRecommendations }) => {
    if (!metrics) return null;
    const { sustainability } = metrics;

    return (
        <div style={{ display: 'grid', gap: '1.5rem' }}>
            {/* Sustainability Card */}
            <div style={{
                backgroundColor: 'var(--color-surface)',
                padding: '1.5rem',
                borderRadius: 'var(--radius)',
                boxShadow: 'var(--shadow-lg)',
                borderLeft: '4px solid var(--color-success)'
            }}>
                <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: 0, color: 'var(--color-success)' }}>
                    <Leaf size={20} />
                    Sürdürülebilirlik Etkisi (Aylık)
                </h2>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div>
                        <div style={{ color: 'var(--color-text-muted)' }}>
                            {sustainability.is_saving ? 'Su Tasarrufu' : 'Su Aşımı'}
                        </div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{Math.abs(sustainability.water || 0).toFixed(1)} L</div>
                    </div>
                    <div>
                        <div style={{ color: 'var(--color-text-muted)', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                            <Leaf size={14} title="CO2 bazlı hesaplama" />
                            {sustainability.is_saving ? 'Ağaç Kazancı' : 'Emisyon Artışı'}
                        </div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{Math.abs(sustainability.trees || 0).toFixed(2)} 🌲</div>
                    </div>
                </div>
                <div style={{ marginTop: '0.5rem', fontStyle: 'italic', color: 'var(--color-text-muted)' }}>
                    "{sustainability.text}"
                </div>
            </div>

            {/* Manual Sustainability Card */}
            {metrics.manual_sustainability && (
                <div style={{
                    backgroundColor: 'var(--color-surface)',
                    padding: '1.5rem',
                    borderRadius: 'var(--radius)',
                    boxShadow: 'var(--shadow-lg)',
                    borderLeft: '4px solid #f97316'
                }}>
                    <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: 0, color: '#f97316' }}>
                        <Droplets size={20} />
                        Sürdürülebilirlik Etkisi - Manuel (Aylık)
                    </h2>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                        <div>
                            <div style={{ color: 'var(--color-text-muted)' }}>
                                {metrics.manual_sustainability.is_saving ? 'Su Tasarrufu' : 'Su Aşımı'}
                            </div>
                            <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{Math.abs(metrics.manual_sustainability.water || 0).toFixed(1)} L</div>
                        </div>
                        <div>
                            <div style={{ color: 'var(--color-text-muted)', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                                <Leaf size={14} title="CO2 bazlı hesaplama" />
                                {metrics.manual_sustainability.is_saving ? 'Ağaç Kazancı' : 'Emisyon Artışı'}
                            </div>
                            <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{Math.abs(metrics.manual_sustainability.trees || 0).toFixed(2)} 🌲</div>
                        </div>
                    </div>
                    <div style={{ marginTop: '0.5rem', fontStyle: 'italic', color: 'var(--color-text-muted)' }}>
                        "{metrics.manual_sustainability.text}"
                    </div>
                </div>
            )}

            {/* Recommendations Card */}
            <div style={{
                backgroundColor: 'var(--color-surface)',
                padding: '1.5rem',
                borderRadius: 'var(--radius)',
                boxShadow: 'var(--shadow-lg)'
            }}>
                <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: 0 }}>
                    <Lightbulb size={20} color="#f59e0b" />
                    Yapay Zeka Önerileri
                </h2>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {frozenRecommendations.length > 0 ? frozenRecommendations.map((rec, i) => (
                        <div key={i} style={{
                            fontSize: '0.95rem',
                            lineHeight: '1.5',
                            color: rec.startsWith('•') ? 'var(--color-primary)' : 'var(--color-text)',
                            paddingLeft: rec.startsWith('•') ? '1rem' : '0',
                            fontWeight: rec.includes('Merhaba') || rec.includes('Böylelikle') ? 'bold' : 'normal'
                        }}>
                            {rec}
                        </div>
                    )) : (
                        <div style={{ color: 'var(--color-text-muted)' }}>Analiz donduruldu. Güncel karne için butona basınız.</div>
                    )}
                </div>
            </div>
        </div >
    );
};
