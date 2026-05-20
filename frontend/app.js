const API_BASE = 'http://localhost:8000';

let currentBookingId = null;
let simulationStep = 1;

async function simulateProgress() {
    const statuses = ['provider_notified', 'en_route', 'completed'];
    const stepIds = ['ss2', 'ss3', 'ss4'];
    const lineIds = ['sl1', 'sl2', 'sl3'];
    const btn = document.querySelector('.simulate-btn');
    btn.disabled = true;

    for (let i = 0; i < statuses.length; i++) {
        await new Promise(r => setTimeout(r, 1500));

        // Call backend
        try {
            const res = await fetch(`${API}/update-status`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    booking_id: currentBookingId,
                    status: statuses[i]
                })
            });
            const data = await res.json();
            allLogs = [...allLogs, ...data.logs];
            renderLogs(allLogs);
        } catch (e) { }

        // Update UI
        document.getElementById(lineIds[i]).classList.add('active');
        document.getElementById(stepIds[i]).className = 'status-step done';
        document.getElementById(stepIds[i]).querySelector('.status-dot').textContent = '✓';

        if (statuses[i] === 'completed') {
            showToast('✓ Service completed successfully!');
        } else {
            showToast('Status updated: ' + statuses[i].replace('_', ' '));
        }
    }

    btn.textContent = '✓ Simulation Complete';
}

const elements = {
    userInput: document.getElementById('userInput'),
    orchestrateBtn: document.getElementById('orchestrateBtn'),
    providersGrid: document.getElementById('providersGrid'),
    logsContainer: document.getElementById('logsContainer'),
    intentBadge: document.getElementById('intentBadge'),
    bookingModal: document.getElementById('bookingModal'),
    modalBody: document.getElementById('modalBody'),
    closeModal: document.querySelector('.close-modal'),
    clearLogs: document.getElementById('clearLogs'),
    toast: document.getElementById('toast')
};

let currentOrchestration = null;

// Add log entry
function addLog(message, type = 'system') {
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    entry.textContent = `> ${message}`;
    elements.logsContainer.appendChild(entry);
    elements.logsContainer.scrollTop = elements.logsContainer.scrollHeight;
}

// Show toast
function showToast(message) {
    elements.toast.textContent = message;
    elements.toast.classList.add('show');
    setTimeout(() => elements.toast.classList.remove('show'), 3000);
}

// Orchestration Logic
async function handleOrchestrate() {
    const input = elements.userInput.value.trim();
    if (!input) return;

    elements.orchestrateBtn.disabled = true;
    addLog(`Initiating orchestration for: "${input}"`, 'system');
    elements.providersGrid.innerHTML = '<div class="empty-state">Orchestrating...</div>';

    try {
        const response = await fetch(`${API_BASE}/orchestrate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_input: input })
        });

        const data = await response.json();

        // Process logs
        if (data.logs) {
            data.logs.forEach(log => addLog(log, 'action'));
        }

        if (!data.success) {
            addLog(data.message, 'error');
            elements.providersGrid.innerHTML = `<div class="empty-state">${data.message}</div>`;
            return;
        }

        currentOrchestration = data;
        displayProviders(data.providers);

        // Show intent badge
        if (data.intent.service_type) {
            elements.intentBadge.textContent = data.intent.service_type;
            elements.intentBadge.style.display = 'block';
        }

    } catch (err) {
        addLog(`Network error: ${err.message}`, 'error');
    } finally {
        elements.orchestrateBtn.disabled = false;
    }
}

function displayProviders(providers) {
    elements.providersGrid.innerHTML = '';

    providers.forEach((p, index) => {
        const card = document.createElement('div');
        card.className = 'provider-card';
        card.innerHTML = `
            <div class="rank-badge">${index + 1}</div>
            <div class="provider-info">
                <h3>${p.name}</h3>
                <div class="meta">
                    <span>📍 ${p.area}</span>
                    <span>⭐ ${p.rating}</span>
                </div>
                <div class="score-box">
                    <div class="score-label">Match Score</div>
                    <div class="score-value">${p.score}</div>
                    <div class="reasoning">${p.reasoning}</div>
                </div>
                <button class="book-now" onclick="openBooking(${p.id})">Select Service</button>
            </div>
        `;
        elements.providersGrid.appendChild(card);
    });
}

// Booking Logic
window.openBooking = (providerId) => {
    const provider = currentOrchestration.providers.find(p => p.id === providerId);
    if (!provider) return;

    elements.modalBody.innerHTML = `
        <div class="booking-details">
            <p><strong>Provider:</strong> ${provider.name}</p>
            <p><strong>Service:</strong> ${provider.service_type}</p>
            <p><strong>Location:</strong> ${provider.area}</p>
            <p style="margin-top: 1rem;">Select a time slot:</p>
            <div class="slot-grid">
                ${provider.available_slots.map(slot => `
                    <button class="slot-btn" onclick="selectSlot(this, '${slot}')">${slot}</button>
                `).join('')}
            </div>
            <button id="confirmBtn" class="book-now" style="margin-top: 2rem;" disabled>Confirm Booking</button>
        </div>
    `;

    let selectedSlot = null;
    window.selectSlot = (btn, slot) => {
        document.querySelectorAll('.slot-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        selectedSlot = slot;
        document.getElementById('confirmBtn').disabled = false;

        document.getElementById('confirmBtn').onclick = () => handleBooking(provider, selectedSlot);
    };

    elements.bookingModal.style.display = 'flex';
};

async function handleBooking(provider, slot) {
    addLog(`Initiating booking for ${provider.name} at ${slot}`, 'system');
    elements.bookingModal.style.display = 'none';

    try {
        const response = await fetch(`${API_BASE}/book-service`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                provider: provider,
                time_slot: slot,
                service_type: provider.service_type
            })
        });

        const data = await response.json();

        if (data.logs) {
            data.logs.forEach(log => addLog(log, 'action'));
        }

        if (data.success) {
            addLog(`Booking Confirmed! ID: ${data.booking.booking_id}`, 'action');
            addLog(`Reminder scheduled: ${data.reminder}`, 'system');
            showToast("Booking Confirmed Successfully!");
        }

    } catch (err) {
        addLog(`Booking failed: ${err.message}`, 'error');
    }
}

// Event Listeners
elements.orchestrateBtn.addEventListener('click', handleOrchestrate);
elements.userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleOrchestrate();
});

elements.closeModal.addEventListener('click', () => {
    elements.bookingModal.style.display = 'none';
});

elements.clearLogs.addEventListener('click', () => {
    elements.logsContainer.innerHTML = '<div class="log-entry system">Logs cleared.</div>';
});

// Close modal on outside click
window.onclick = (event) => {
    if (event.target == elements.bookingModal) {
        elements.bookingModal.style.display = 'none';
    }
};
