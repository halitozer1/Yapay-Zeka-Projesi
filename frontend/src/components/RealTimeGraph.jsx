
import React, { useEffect, useState, useRef } from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { api } from '../api';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler
);

export const RealTimeGraph = ({ onSkip, onResume, isPaused }) => {
    const [chartData, setChartData] = useState({
        datasets: [],
    });
    const [liveCost, setLiveCost] = useState(0);

    // Polling refs to handle intervals
    const intervalRef = useRef(null);

    const fetchData = async () => {
        try {
            const data = await api.getStream();

            const labels = data.map(d => new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
            const values = data.map(d => d.usage);
            const manualValues = data.map(d => d.manual_usage || 0);
            const statuses = data.map(d => d.status);
            const references = data.map(d => d.reference);
            const costs = data.map(d => d.cost);

            if (costs.length > 0) {
                setLiveCost(costs[costs.length - 1]);
            }

            setChartData({
                labels,
                datasets: [
                    {
                        label: 'Su Kullanımı (L)',
                        data: values,
                        borderColor: '#3b82f6',
                        segment: {
                            borderColor: ctx => {
                                // Color the segment based on the status of the *end* point (or start)
                                const index = ctx.p1DataIndex;
                                const status = statuses[index];
                                if (status === 'high') return '#ef4444'; // Red
                                if (status === 'low') return '#22c55e'; // Green
                                return '#3b82f6'; // Blue
                            }
                        },
                        costs: costs, // Custom field for tooltip
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointRadius: 4,
                        pointBackgroundColor: statuses.map(s => {
                            if (s === 'high') return '#ef4444';
                            if (s === 'low') return '#22c55e';
                            return '#3b82f6';
                        })
                    },
                    {
                        label: 'Referans Limit',
                        data: references,
                        borderColor: '#94a3b8',
                        borderDash: [5, 5],
                        pointRadius: 0,
                        fill: false
                    }
                ]
            });
        } catch (e) {
            console.error(e);
        }
    };

    useEffect(() => {
        fetchData();
        intervalRef.current = setInterval(() => {
            if (!isPaused) fetchData();
        }, 1500);

        return () => {
            if (intervalRef.current) clearInterval(intervalRef.current);
        };
    }, [isPaused]);

    const handleAction = async () => {
        if (isPaused) {
            if (onResume) await onResume();
        } else {
            if (onSkip) await onSkip();
        }
        fetchData();
    };

    const options = {
        responsive: true,
        plugins: {
            legend: {
                position: 'top',
                labels: { color: '#94a3b8' }
            },
            title: {
                display: false // We will use a custom header
            },
            tooltip: {
                callbacks: {
                    label: function (context) {
                        let label = context.dataset.label || '';
                        if (label) {
                            label += ': ';
                        }
                        if (context.parsed.y !== null) {
                            label += context.parsed.y.toFixed(1) + ' L';
                        }
                        // Add cost for system usage dataset
                        if (context.datasetIndex === 0 && context.dataset.costs) {
                            const cost = context.dataset.costs[context.dataIndex];
                            label += ` (${cost.toFixed(2)} ₺)`;
                        }
                        return label;
                    }
                }
            }
        },
        scales: {
            y: {
                grid: { color: '#334155' },
                ticks: { color: '#94a3b8' }
            },
            x: {
                grid: { display: false },
                ticks: { color: '#94a3b8' }
            }
        },
        animation: {
            duration: 500, // Smooth flow
            easing: 'linear'
        }
    };

    return (
        <div style={{ backgroundColor: 'var(--color-surface)', padding: '1.5rem', borderRadius: 'var(--radius)', boxShadow: 'var(--shadow-lg)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                <h3 style={{ margin: 0, color: '#f8fafc' }}>Canlı Su Kullanım Akışı</h3>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(59, 130, 246, 0.15)', padding: '0.4rem 0.8rem', borderRadius: '2rem', border: '1px solid rgba(59, 130, 246, 0.3)' }}>
                        <span style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem', fontWeight: '600' }}>ANLIK MALİYET:</span>
                        <span style={{ color: '#3b82f6', fontWeight: '800', fontSize: '1.1rem' }}>{liveCost.toFixed(2)} ₺</span>
                    </div>
                    <button
                        onClick={handleAction}
                        style={{
                            fontSize: '0.75rem',
                            padding: '0.25rem 0.75rem',
                            background: isPaused ? '#10b981' : '#1e293b',
                            color: isPaused ? 'white' : '#60a5fa',
                            border: isPaused ? '1px solid #059669' : '1px solid #334155',
                            borderRadius: '1rem',
                            cursor: 'pointer',
                            fontWeight: 'bold',
                            transition: 'all 0.2s',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem'
                        }}
                        onMouseOver={(e) => e.currentTarget.style.filter = 'brightness(1.1)'}
                        onMouseOut={(e) => e.currentTarget.style.filter = 'brightness(1)'}
                    >
                        {isPaused ? '▶️ Devam Et (Yeni Dönem)' : '⏭️ Ayı Tamamla (Raporla)'}
                    </button>
                </div>
            </div>
            <Line options={options} data={chartData} />
        </div>
    );
};
