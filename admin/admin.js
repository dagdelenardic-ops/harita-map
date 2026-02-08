// Global state
let eventsData = {
    categories: {},
    events: []
};
let filteredEvents = [];
let deleteEventId = null;

// Category labels
const categoryLabels = {
    war: 'Savas/Catisma',
    genocide: 'Soykirim',
    revolution: 'Devrim/Rejim Degisikligi',
    terror: 'Teror Saldirisi',
    leader: 'Onemli Lider'
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadData();
});

// Load data from localStorage or default
function loadData() {
    const stored = localStorage.getItem('geopoliticalEvents');
    if (stored) {
        eventsData = JSON.parse(stored);
    } else {
        // Try to load from file path (for local development)
        fetchDefaultData();
        return;
    }
    initializeUI();
}

// Fetch default data from events.json
async function fetchDefaultData() {
    try {
        const response = await fetch('../data/events.json');
        if (response.ok) {
            eventsData = await response.json();
            saveData();
        }
    } catch (e) {
        console.log('Could not load default data, starting fresh');
        eventsData = {
            categories: {
                war: { label: 'Savas/Catisma', icon: 'fa-fire', color: '#e74c3c' },
                genocide: { label: 'Soykirim', icon: 'fa-skull', color: '#2c3e50' },
                revolution: { label: 'Devrim/Rejim Degisikligi', icon: 'fa-flag', color: '#e67e22' },
                terror: { label: 'Teror Saldirisi', icon: 'fa-bomb', color: '#9b59b6' },
                leader: { label: 'Onemli Lider', icon: 'fa-user', color: '#3498db' }
            },
            events: []
        };
    }
    initializeUI();
}

// Save data to localStorage
function saveData() {
    localStorage.setItem('geopoliticalEvents', JSON.stringify(eventsData));
}

// Initialize UI
function initializeUI() {
    populateCountryFilter();
    applyFilters();
    updateStats();
}

// Populate country filter dropdown
function populateCountryFilter() {
    const countries = [...new Set(eventsData.events.map(e => e.country_name))].sort();
    const select = document.getElementById('filterCountry');
    select.innerHTML = '<option value="">Tumu</option>';
    countries.forEach(country => {
        const option = document.createElement('option');
        option.value = country;
        option.textContent = country;
        select.appendChild(option);
    });
}

// Apply filters and render table
function applyFilters() {
    const country = document.getElementById('filterCountry').value;
    const decade = document.getElementById('filterDecade').value;
    const category = document.getElementById('filterCategory').value;
    const search = document.getElementById('filterSearch').value.toLowerCase();

    filteredEvents = eventsData.events.filter(event => {
        if (country && event.country_name !== country) return false;
        if (decade && event.decade !== decade) return false;
        if (category && event.category !== category) return false;
        if (search && !event.title.toLowerCase().includes(search)) return false;
        return true;
    });

    // Sort by year descending
    filteredEvents.sort((a, b) => b.year - a.year);

    renderTable();
}

// Render events table
function renderTable() {
    const tbody = document.getElementById('eventsBody');
    const noResults = document.getElementById('noResults');
    const table = document.getElementById('eventsTable');

    if (filteredEvents.length === 0) {
        table.style.display = 'none';
        noResults.style.display = 'block';
        return;
    }

    table.style.display = '';
    noResults.style.display = 'none';

    tbody.innerHTML = filteredEvents.map(event => `
        <tr>
            <td><strong>${event.country_name}</strong><br><small style="color:#666">${event.country_code}</small></td>
            <td>${event.year}<br><small style="color:#666">${event.decade}</small></td>
            <td><span class="category-badge category-${event.category}">${categoryLabels[event.category] || event.category}</span></td>
            <td><strong>${event.title}</strong></td>
            <td class="truncate" title="${event.description}">${event.description}</td>
            <td>
                <div class="action-btns">
                    <button class="action-btn edit" onclick="editEvent('${event.id}')" title="Duzenle">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="action-btn delete" onclick="deleteEvent('${event.id}')" title="Sil">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

// Update statistics
function updateStats() {
    const events = eventsData.events;
    const countries = new Set(events.map(e => e.country_name));

    document.getElementById('totalEvents').textContent = events.length;
    document.getElementById('totalCountries').textContent = countries.size;
    document.getElementById('totalWars').textContent = events.filter(e => e.category === 'war').length;
    document.getElementById('totalGenocides').textContent = events.filter(e => e.category === 'genocide').length;
    document.getElementById('totalRevolutions').textContent = events.filter(e => e.category === 'revolution').length;
}

// Generate unique ID
function generateId() {
    return 'ev' + Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
}

// Open modal for new event
function openModal() {
    document.getElementById('modalTitle').textContent = 'Yeni Olay Ekle';
    document.getElementById('eventForm').reset();
    document.getElementById('eventId').value = '';
    document.getElementById('eventModal').classList.add('active');
}

// Close modal
function closeModal() {
    document.getElementById('eventModal').classList.remove('active');
}

// Edit event
function editEvent(id) {
    const event = eventsData.events.find(e => e.id === id);
    if (!event) return;

    document.getElementById('modalTitle').textContent = 'Olay Duzenle';
    document.getElementById('eventId').value = event.id;
    document.getElementById('countryName').value = event.country_name;
    document.getElementById('countryCode').value = event.country_code;
    document.getElementById('eventLat').value = event.lat;
    document.getElementById('eventLon').value = event.lon;
    document.getElementById('eventYear').value = event.year;
    document.getElementById('eventDecade').value = event.decade;
    document.getElementById('eventCategory').value = event.category;
    document.getElementById('eventTitle').value = event.title;
    document.getElementById('eventDescription').value = event.description;
    document.getElementById('eventWikipedia').value = event.wikipedia_url || '';
    document.getElementById('eventCasualties').value = event.casualties || '';
    document.getElementById('eventKeyFigures').value = (event.key_figures || []).join(', ');

    document.getElementById('eventModal').classList.add('active');
}

// Save event (create or update)
function saveEvent(e) {
    e.preventDefault();

    const id = document.getElementById('eventId').value;
    const keyFiguresStr = document.getElementById('eventKeyFigures').value;
    const keyFigures = keyFiguresStr ? keyFiguresStr.split(',').map(s => s.trim()).filter(s => s) : [];

    const eventData = {
        id: id || generateId(),
        country_code: document.getElementById('countryCode').value.toUpperCase(),
        country_name: document.getElementById('countryName').value,
        lat: parseFloat(document.getElementById('eventLat').value),
        lon: parseFloat(document.getElementById('eventLon').value),
        decade: document.getElementById('eventDecade').value,
        year: parseInt(document.getElementById('eventYear').value),
        category: document.getElementById('eventCategory').value,
        title: document.getElementById('eventTitle').value,
        description: document.getElementById('eventDescription').value,
        wikipedia_url: document.getElementById('eventWikipedia').value || null,
        casualties: document.getElementById('eventCasualties').value ? parseInt(document.getElementById('eventCasualties').value) : null,
        key_figures: keyFigures
    };

    if (id) {
        // Update existing
        const index = eventsData.events.findIndex(e => e.id === id);
        if (index !== -1) {
            eventsData.events[index] = eventData;
        }
    } else {
        // Add new
        eventsData.events.push(eventData);
    }

    saveData();
    closeModal();
    populateCountryFilter();
    applyFilters();
    updateStats();
}

// Delete event - show confirmation
function deleteEvent(id) {
    const event = eventsData.events.find(e => e.id === id);
    if (!event) return;

    deleteEventId = id;
    document.getElementById('deleteEventTitle').textContent = event.title;
    document.getElementById('deleteModal').classList.add('active');
}

// Close delete modal
function closeDeleteModal() {
    document.getElementById('deleteModal').classList.remove('active');
    deleteEventId = null;
}

// Confirm delete
function confirmDelete() {
    if (!deleteEventId) return;

    eventsData.events = eventsData.events.filter(e => e.id !== deleteEventId);
    saveData();
    closeDeleteModal();
    populateCountryFilter();
    applyFilters();
    updateStats();
}

// Export JSON
function exportJSON() {
    const dataStr = JSON.stringify(eventsData, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = 'events.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Import JSON
function importJSON(e) {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
        try {
            const imported = JSON.parse(event.target.result);
            if (imported.events && Array.isArray(imported.events)) {
                eventsData = imported;
                saveData();
                initializeUI();
                alert('Veriler basariyla yuklendi!');
            } else {
                alert('Gecersiz dosya formati!');
            }
        } catch (err) {
            alert('JSON dosyasi okunamadi: ' + err.message);
        }
    };
    reader.readAsText(file);
    e.target.value = '';
}

// Auto-calculate decade from year
document.getElementById('eventYear')?.addEventListener('change', function() {
    const year = parseInt(this.value);
    if (year >= 1920 && year <= 2029) {
        const decadeStart = Math.floor(year / 10) * 10;
        document.getElementById('eventDecade').value = decadeStart + 's';
    }
});
