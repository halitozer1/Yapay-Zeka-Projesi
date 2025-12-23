
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

export const WeeklyChart = ({ metrics }) => {
    if (!metrics || !metrics.stats || !metrics.stats.daily || !metrics.stats.daily.usage_system) {
        return <div style={{ color: 'var(--color-text-muted)', padding: '1rem' }}>Yükleniyor...</div>;
    }

    const { usage_system, usage_manual } = metrics.stats.daily;

    // Get unique dates from both sources, sort them
    const allDates = Array.from(new Set([
        ...Object.keys(usage_system),
        ...Object.keys(usage_manual || {})
    ])).sort();

    // Take last 7 days
    const last7Days = allDates.slice(-7);

    const data = {
        labels: last7Days,
        datasets: [
            {
                label: 'Sistem Verisi (L)',
                data: last7Days.map(date => usage_system[date] || 0),
                backgroundColor: 'rgba(59, 130, 246, 0.6)',
                borderColor: '#3b82f6',
                borderWidth: 1,
            },
            {
                label: 'Manuel Giriş (L)',
                data: last7Days.map(date => usage_manual[date] || 0),
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
                text: 'Haftalık Kullanım Kıyaslaması (Son 7 Gün)',
                color: '#f8fafc'
            },
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: { color: '#334155' },
                ticks: { color: '#94a3b8' }
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
