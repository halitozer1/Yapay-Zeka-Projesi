
import React from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend
);

export const WeeklyCostChart = ({ metrics }) => {
    if (!metrics || !metrics.stats || !metrics.stats.daily || !metrics.stats.daily.cost_system) {
        return <div style={{ color: 'var(--color-text-muted)', padding: '1rem' }}>Maliyet verileri yükleniyor...</div>;
    }

    const { cost_system, cost_manual } = metrics.stats.daily;

    // Get unique dates from both sources, sort them
    const allDates = Array.from(new Set([
        ...Object.keys(cost_system),
        ...Object.keys(cost_manual || {})
    ])).sort();

    // Take last 7 days
    const last7Days = allDates.slice(-7);

    const data = {
        labels: last7Days,
        datasets: [
            {
                label: 'Sistem Maliyeti (₺)',
                data: last7Days.map(date => cost_system[date] || 0),
                backgroundColor: 'rgba(56, 189, 248, 0.6)',
                borderColor: '#0ea5e9',
                borderWidth: 1,
            },
            {
                label: 'Manuel Giriş Maliyeti (₺)',
                data: last7Days.map(date => cost_manual[date] || 0),
                backgroundColor: 'rgba(249, 115, 22, 0.6)',
                borderColor: '#f97316',
                borderWidth: 1,
            }
        ]
    };

    const options = {
        responsive: true,
        plugins: {
            legend: {
                position: 'top',
                labels: { color: '#94a3b8' }
            },
            title: {
                display: true,
                text: 'Haftalık Maliyet Analizi (₺)',
                color: '#f8fafc'
            },
            tooltip: {
                callbacks: {
                    label: function (context) {
                        return `${context.dataset.label}: ${context.parsed.y.toFixed(2)} ₺`;
                    }
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: { color: '#334155' },
                ticks: {
                    color: '#94a3b8',
                    callback: function (value) {
                        return value + ' ₺';
                    }
                }
            },
            x: {
                grid: { display: false },
                ticks: { color: '#94a3b8' }
            }
        }
    };

    return (
        <div style={{ backgroundColor: 'var(--color-surface)', padding: '1.5rem', borderRadius: 'var(--radius)', boxShadow: 'var(--shadow-lg)' }}>
            <Bar options={options} data={data} />
        </div>
    );
};
