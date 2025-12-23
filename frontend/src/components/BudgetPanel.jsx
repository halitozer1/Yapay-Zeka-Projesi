import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { Wallet, AlertTriangle, CheckCircle } from 'lucide-react';

export const BudgetPanel = ({ metrics, onUpdate }) => {
    const [budgetInput, setBudgetInput] = useState('');
    const [waterInput, setWaterInput] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSetBudget = async (e) => {
        e.preventDefault();
        if (!budgetInput) return;
        setLoading(true);
        try {
            await api.setBudget(parseFloat(budgetInput));
            setBudgetInput('');
            onUpdate(); // Trigger refresh
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleSetWaterLimit = async (e) => {
        e.preventDefault();
        if (!waterInput) return;
        setLoading(true);
        try {
            await api.setWaterLimit(parseFloat(waterInput));
            setWaterInput('');
            onUpdate(); // Trigger refresh
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    if (!metrics || !metrics.stats) return null;

    const { stats, budget } = metrics;
    const { system, manual } = stats;

    const renderBudgetSection = (title, data, color) => {
        const { total_cost, total_usage, projection, weeks, percent, is_over } = data;

        let progressColor = color;
        if (percent > 80) progressColor = '#f59e0b';
        if (percent > 100) progressColor = 'var(--color-danger)';

        return (
            <div style={{ marginBottom: '2rem', borderBottom: '1px solid #1e293b', paddingBottom: '1.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                    <h3 style={{ margin: 0, fontSize: '1.1rem', color: '#f8fafc' }}>{title}</h3>
                    <div style={{ fontSize: '0.75rem', background: '#1e293b', padding: '0.2rem 0.6rem', borderRadius: '1rem', color: 'var(--color-text-muted)' }}>
                        {weeks} Haftalık Veri
                    </div>
                </div>

                {/* Prominent Current Stats */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
                    <div style={{ background: 'rgba(30, 41, 59, 0.5)', padding: '0.75rem', borderRadius: '0.5rem' }}>
                        <div style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem', marginBottom: '0.25rem' }}>Kullanım Tutarı</div>
                        <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: is_over ? 'var(--color-danger)' : color }}>
                            {total_cost.toFixed(2)} ₺
                        </div>
                    </div>
                    <div style={{ background: 'rgba(30, 41, 59, 0.5)', padding: '0.75rem', borderRadius: '0.5rem' }}>
                        <div style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem', marginBottom: '0.25rem' }}>Kullanım Miktarı</div>
                        <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#f8fafc' }}>
                            {total_usage.toFixed(0)} L
                        </div>
                    </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--color-text-muted)', marginBottom: '0.4rem' }}>
                    <span>Tahmini Aylık: {projection.toFixed(2)} ₺</span>
                    <span style={{ fontWeight: '600', color: '#94a3b8' }}>Max Bütçe: {budget.toFixed(2)} ₺</span>
                </div>

                {/* Progress Bar */}
                <div style={{
                    height: '6px',
                    width: '100%',
                    backgroundColor: '#0f172a',
                    borderRadius: '3px',
                    overflow: 'hidden',
                    border: '1px solid #1e293b'
                }}>
                    <div style={{
                        height: '100%',
                        width: `${Math.min(percent, 100)}%`,
                        backgroundColor: progressColor,
                        transition: 'width 0.5s ease'
                    }} />
                </div>
            </div>
        );
    };

    return (
        <div style={{
            backgroundColor: 'var(--color-surface)',
            padding: '1.5rem',
            borderRadius: 'var(--radius)',
            boxShadow: 'var(--shadow-lg)'
        }}>
            <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: 0, marginBottom: '2rem', paddingBottom: '1rem', borderBottom: '2px solid var(--color-primary)' }}>
                <Wallet size={24} color="var(--color-primary)" />
                Bütçe ve Maliyet Analizi
            </h2>

            {renderBudgetSection("Sistem Verisi (Fatura/Kullanım)", system, "#3b82f6")}
            {renderBudgetSection("Manuel Giriş (Fatura/Kullanım)", manual, "#f97316")}

        </div>
    );
};
