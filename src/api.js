const API_URL = 'http://localhost:8000';

export const api = {
    getMetrics: async () => {
        const response = await fetch(`${API_URL}/metrics?_t=${Date.now()}`);
        if (!response.ok) throw new Error('Failed to fetch metrics');
        return response.json();
    },
    getStream: async () => {
        const response = await fetch(`${API_URL}/stream?_t=${Date.now()}`);
        if (!response.ok) throw new Error('Failed to fetch stream');
        return response.json();
    },
    getRecommendations: async () => {
        const response = await fetch(`${API_URL}/recommendations`);
        if (!response.ok) throw new Error('Failed to fetch recommendations');
        return response.json();
    },
    setBudget: async (amount) => {
        const response = await fetch(`${API_URL}/budget`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount }),
        });
        if (!response.ok) throw new Error('Failed to set budget');
        return response.json();
    },
    addManualEntry: async (date, amount, nightAmount = 0) => {
        const response = await fetch(`${API_URL}/usage/manual`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ date, amount, night_amount: nightAmount }),
        });
        if (!response.ok) throw new Error('Failed to add entry');
        return response.json();
    },

    deleteManualEntry: async (date) => {
        const response = await fetch(`${API_URL}/usage/manual/${date}`, {
            method: 'DELETE',
        });
        if (!response.ok) throw new Error('Failed to delete entry');
        return response.json();
    },
    setWaterLimit: async (amount) => {
        const response = await fetch(`${API_URL}/limit/water`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount }),
        });
        if (!response.ok) throw new Error('Failed to set water limit');
        return response.json();
    },
    skipSimulation: async () => {
        const response = await fetch(`${API_URL}/simulation/skip`, {
            method: 'POST',
        });
        if (!response.ok) throw new Error('Failed to skip simulation');
        return response.json();
    },
    resumeSimulation: async () => {
        const response = await fetch(`${API_URL}/simulation/resume`, {
            method: 'POST',
        });
        if (!response.ok) throw new Error('Failed to resume simulation');
        return response.json();
    },
    sendChatMessage: async (message) => {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message }),
        });
        if (!response.ok) throw new Error('Failed to send message');
        return response.json();
    },
};
