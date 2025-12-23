import React, { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send, Bot, User } from 'lucide-react';
import { api } from '../api';

export function Chatbot() {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState([
        {
            role: 'bot',
            content: 'Merhaba! 👋 Ben su tasarrufu asistanınızım. Size su kullanımınız, tasarruf önerileri veya fatura analizi konusunda yardımcı olabilirim. Ne sormak istersiniz?'
        }
    ]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async () => {
        if (!inputValue.trim() || isLoading) return;

        const userMessage = inputValue.trim();
        setInputValue('');

        // Add user message
        setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
        setIsLoading(true);

        try {
            const response = await api.sendChatMessage(userMessage);
            setMessages(prev => [...prev, { role: 'bot', content: response.response }]);
        } catch (error) {
            setMessages(prev => [...prev, {
                role: 'bot',
                content: 'Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.'
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <>
            {/* Floating Button */}
            {!isOpen && (
                <button
                    onClick={() => setIsOpen(true)}
                    style={{
                        position: 'fixed',
                        bottom: '24px',
                        right: '24px',
                        width: '60px',
                        height: '60px',
                        borderRadius: '50%',
                        background: 'linear-gradient(135deg, #3b82f6, #06b6d4)',
                        border: 'none',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        boxShadow: '0 4px 20px rgba(59, 130, 246, 0.4)',
                        transition: 'transform 0.2s, box-shadow 0.2s',
                        zIndex: 1000,
                    }}
                    onMouseEnter={(e) => {
                        e.target.style.transform = 'scale(1.1)';
                        e.target.style.boxShadow = '0 6px 25px rgba(59, 130, 246, 0.5)';
                    }}
                    onMouseLeave={(e) => {
                        e.target.style.transform = 'scale(1)';
                        e.target.style.boxShadow = '0 4px 20px rgba(59, 130, 246, 0.4)';
                    }}
                >
                    <MessageCircle size={28} color="white" />
                </button>
            )}

            {/* Chat Window */}
            {isOpen && (
                <div
                    style={{
                        position: 'fixed',
                        bottom: '24px',
                        right: '24px',
                        width: '380px',
                        height: '520px',
                        background: 'var(--color-surface)',
                        borderRadius: '16px',
                        boxShadow: '0 10px 40px rgba(0, 0, 0, 0.3)',
                        display: 'flex',
                        flexDirection: 'column',
                        overflow: 'hidden',
                        zIndex: 1000,
                        border: '1px solid rgba(59, 130, 246, 0.2)',
                    }}
                >
                    {/* Header */}
                    <div
                        style={{
                            background: 'linear-gradient(135deg, #3b82f6, #06b6d4)',
                            padding: '16px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                        }}
                    >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <Bot size={24} color="white" />
                            <div>
                                <div style={{ fontWeight: 'bold', color: 'white' }}>Su Asistanı</div>
                                <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.8)' }}>
                                    Çevrimiçi
                                </div>
                            </div>
                        </div>
                        <button
                            onClick={() => setIsOpen(false)}
                            style={{
                                background: 'rgba(255,255,255,0.2)',
                                border: 'none',
                                borderRadius: '50%',
                                width: '32px',
                                height: '32px',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                            }}
                        >
                            <X size={18} color="white" />
                        </button>
                    </div>

                    {/* Messages */}
                    <div
                        style={{
                            flex: 1,
                            overflowY: 'auto',
                            padding: '16px',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '12px',
                        }}
                    >
                        {messages.map((msg, idx) => (
                            <div
                                key={idx}
                                style={{
                                    display: 'flex',
                                    justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                                    gap: '8px',
                                }}
                            >
                                {msg.role === 'bot' && (
                                    <div
                                        style={{
                                            width: '32px',
                                            height: '32px',
                                            borderRadius: '50%',
                                            background: 'linear-gradient(135deg, #3b82f6, #06b6d4)',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            flexShrink: 0,
                                        }}
                                    >
                                        <Bot size={18} color="white" />
                                    </div>
                                )}
                                <div
                                    style={{
                                        maxWidth: '75%',
                                        padding: '10px 14px',
                                        borderRadius: msg.role === 'user'
                                            ? '16px 16px 4px 16px'
                                            : '16px 16px 16px 4px',
                                        background: msg.role === 'user'
                                            ? 'linear-gradient(135deg, #3b82f6, #06b6d4)'
                                            : 'rgba(255,255,255,0.05)',
                                        color: 'white',
                                        fontSize: '0.9rem',
                                        lineHeight: '1.5',
                                        whiteSpace: 'pre-wrap',
                                    }}
                                >
                                    {msg.content}
                                </div>
                                {msg.role === 'user' && (
                                    <div
                                        style={{
                                            width: '32px',
                                            height: '32px',
                                            borderRadius: '50%',
                                            background: '#6366f1',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            flexShrink: 0,
                                        }}
                                    >
                                        <User size={18} color="white" />
                                    </div>
                                )}
                            </div>
                        ))}
                        {isLoading && (
                            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                <div
                                    style={{
                                        width: '32px',
                                        height: '32px',
                                        borderRadius: '50%',
                                        background: 'linear-gradient(135deg, #3b82f6, #06b6d4)',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                    }}
                                >
                                    <Bot size={18} color="white" />
                                </div>
                                <div
                                    style={{
                                        padding: '10px 14px',
                                        borderRadius: '16px 16px 16px 4px',
                                        background: 'rgba(255,255,255,0.05)',
                                        color: 'white',
                                        fontSize: '0.9rem',
                                    }}
                                >
                                    <div style={{ display: 'flex', gap: '4px' }}>
                                        <span className="typing-dot">•</span>
                                        <span className="typing-dot" style={{ animationDelay: '0.2s' }}>•</span>
                                        <span className="typing-dot" style={{ animationDelay: '0.4s' }}>•</span>
                                    </div>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Input */}
                    <div
                        style={{
                            padding: '12px 16px',
                            borderTop: '1px solid rgba(255,255,255,0.1)',
                            display: 'flex',
                            gap: '10px',
                        }}
                    >
                        <input
                            type="text"
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder="Mesajınızı yazın..."
                            style={{
                                flex: 1,
                                padding: '10px 14px',
                                borderRadius: '24px',
                                border: '1px solid rgba(255,255,255,0.1)',
                                background: 'rgba(255,255,255,0.05)',
                                color: 'white',
                                fontSize: '0.9rem',
                                outline: 'none',
                            }}
                        />
                        <button
                            onClick={handleSend}
                            disabled={!inputValue.trim() || isLoading}
                            style={{
                                width: '44px',
                                height: '44px',
                                borderRadius: '50%',
                                background: inputValue.trim()
                                    ? 'linear-gradient(135deg, #3b82f6, #06b6d4)'
                                    : 'rgba(255,255,255,0.1)',
                                border: 'none',
                                cursor: inputValue.trim() ? 'pointer' : 'not-allowed',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                transition: 'all 0.2s',
                            }}
                        >
                            <Send size={20} color={inputValue.trim() ? 'white' : '#666'} />
                        </button>
                    </div>
                </div>
            )}

            <style>{`
                @keyframes typing {
                    0%, 60%, 100% { opacity: 0.3; }
                    30% { opacity: 1; }
                }
                .typing-dot {
                    animation: typing 1.4s infinite;
                }
            `}</style>
        </>
    );
}
