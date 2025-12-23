import React from 'react';
import { Bot, X, Sparkles } from 'lucide-react';

export const ReportModal = ({ isOpen, onClose, recommendations = [] }) => {
    if (!isOpen) return null;

    return (
        <div
            style={{
                position: 'fixed',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                backgroundColor: 'rgba(0, 0, 0, 0.7)',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                zIndex: 1000,
                backdropFilter: 'blur(5px)'
            }}
            onClick={onClose}
        >
            <div
                onClick={(e) => e.stopPropagation()} // Prevent closing when clicking inside modal
                style={{
                    backgroundColor: 'var(--color-surface)',
                    width: '90%',
                    maxWidth: '650px',
                    borderRadius: '1.5rem',
                    position: 'relative',
                    boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
                    border: '1px solid #3b82f6',
                    overflow: 'hidden',
                    animation: 'modalSlideUp 0.3s ease-out',
                    cursor: 'default',
                    maxHeight: '80vh',
                    display: 'flex',
                    flexDirection: 'column'
                }}
            >
                {/* Header Decoration */}
                <div style={{
                    height: '140px',
                    background: 'linear-gradient(135deg, #1d4ed8 0%, #1e3a8a 100%)',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                    alignItems: 'center',
                    color: 'white',
                    position: 'relative',
                    borderBottom: '1px solid rgba(255,255,255,0.1)',
                    flexShrink: 0
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                        <Bot size={48} style={{ color: '#facc15' }} />
                        <Sparkles size={24} style={{ color: '#60a5fa' }} />
                    </div>
                    <h2 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 'bold' }}>Yapay Zeka Analizi</h2>
                    <p style={{ margin: '0.25rem 0 0 0', opacity: 0.8, fontSize: '0.9rem' }}>Size Özel Tasarruf Önerileri</p>

                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            onClose();
                        }}
                        style={{
                            position: 'absolute',
                            top: '1rem',
                            right: '1rem',
                            background: 'white',
                            border: 'none',
                            borderRadius: '12px',
                            width: '40px',
                            height: '40px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: '#1e3a8a',
                            cursor: 'pointer',
                            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.2)',
                            transition: 'all 0.2s ease',
                            zIndex: 100
                        }}
                        onMouseOver={(e) => {
                            e.currentTarget.style.transform = 'scale(1.1) rotate(90deg)';
                            e.currentTarget.style.backgroundColor = '#f1f5f9';
                        }}
                        onMouseOut={(e) => {
                            e.currentTarget.style.transform = 'scale(1) rotate(0deg)';
                            e.currentTarget.style.backgroundColor = 'white';
                        }}
                    >
                        <X size={24} strokeWidth={3} />
                    </button>
                </div>

                <div style={{ padding: '2rem', overflowY: 'auto', flex: 1 }}>
                    <div style={{
                        background: 'rgba(59, 130, 246, 0.05)',
                        padding: '1.5rem',
                        borderRadius: '1rem',
                        marginBottom: '2rem',
                        border: '1px dashed #3b82f6'
                    }}>
                        {recommendations.map((line, idx) => (
                            <div key={idx} style={{
                                marginBottom: '0.75rem',
                                fontSize: '1.05rem',
                                lineHeight: '1.5',
                                color: line.startsWith('•') ? '#60a5fa' : 'white',
                                fontWeight: line.includes('Merhaba') || line.includes('Böylelikle') ? 'bold' : 'normal',
                                paddingLeft: line.startsWith('•') ? '1.5rem' : '0',
                                position: 'relative'
                            }}>
                                {line}
                            </div>
                        ))}
                    </div>

                    <button
                        onClick={onClose}
                        style={{
                            width: '100%',
                            padding: '1rem',
                            backgroundColor: 'var(--color-primary)',
                            color: 'white',
                            border: 'none',
                            borderRadius: 'var(--radius)',
                            fontWeight: 'bold',
                            fontSize: '1.1rem',
                            cursor: 'pointer',
                            transition: 'transform 0.2s',
                            boxShadow: '0 10px 15px -3px rgba(59, 130, 246, 0.3)'
                        }}
                        onMouseOver={(e) => e.currentTarget.style.transform = 'scale(1.02)'}
                        onMouseOut={(e) => e.currentTarget.style.transform = 'scale(1)'}
                    >
                        RAPORU KAPAT
                    </button>
                </div>

                <style>{`
                    @keyframes modalSlideUp {
                        from { transform: translateY(40px); opacity: 0; }
                        to { transform: translateY(0); opacity: 1; }
                    }
                `}</style>
            </div>
        </div>
    );
};
