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
    leader: 'Onemli Lider',
    politics: 'Politika',
    diplomacy: 'Diplomasi',
    culture: 'Kultur & Toplum',
    cinema: 'Sinema',
    music: 'Muzik',
    time_100: 'Time 100'
};

function decadeFromYear(year) {
    const y = Number(year);
    if (!Number.isFinite(y)) return '';
    const d = Math.floor(y / 10) * 10;
    return String(d) + 's';
}

function hexToRgb(hex) {
    const h = String(hex || '').trim().replace(/^#/, '');
    if (h.length !== 6) return null;
    const r = parseInt(h.slice(0, 2), 16);
    const g = parseInt(h.slice(2, 4), 16);
    const b = parseInt(h.slice(4, 6), 16);
    if ([r, g, b].some(x => Number.isNaN(x))) return null;
    return [r, g, b];
}

function rgbaFromHex(hex, alpha) {
    const rgb = hexToRgb(hex);
    if (!rgb) return '';
    const a = Number(alpha);
    const clamped = Number.isFinite(a) ? Math.max(0, Math.min(1, a)) : 1;
    return `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, ${clamped})`;
}

function ensureSelectHasOption(selectEl, value, label) {
    if (!selectEl) return;
    if (value === null || value === undefined) return;
    const v = String(value);
    for (const opt of Array.from(selectEl.options || [])) {
        if (opt.value === v) return;
    }
    const opt = document.createElement('option');
    opt.value = v;
    opt.textContent = label || v;
    selectEl.appendChild(opt);
}

function ensureCategoryDefsInPlace() {
    if (!eventsData || typeof eventsData !== 'object') return;
    if (!eventsData.categories || typeof eventsData.categories !== 'object') {
        eventsData.categories = {};
    }

    const cats = eventsData.categories;
    const used = new Set(
        (eventsData.events || [])
            .map(e => String((e && e.category) || '').trim())
            .filter(Boolean)
    );

    used.forEach(key => {
        if (cats[key]) return;
        if (key === 'politics') {
            cats[key] = { label: 'Politika', icon: 'fa-landmark', color: '#16a085' };
            return;
        }
        if (key === 'cinema') {
            cats[key] = { label: 'Sinema', icon: 'fa-film', color: '#95a5a6' };
            return;
        }
        if (key === 'music') {
            cats[key] = { label: 'Müzik', icon: 'fa-music', color: '#e84393' };
            return;
        }
        cats[key] = { label: categoryLabels[key] || key, icon: 'fa-tag', color: '#7f8c8d' };
    });
}

function getCategoryMeta(key) {
    const k = String(key || '').trim();
    const defs = (eventsData && eventsData.categories && typeof eventsData.categories === 'object') ? eventsData.categories : {};
    const def = defs[k] || {};
    const label = def.label || categoryLabels[k] || k || 'unknown';
    const color = def.color || '#7f8c8d';
    const icon = def.icon || 'fa-tag';
    return { key: k, label, color, icon };
}

function renderCategoryBadge(categoryKey) {
    const meta = getCategoryMeta(categoryKey);
    const bg = rgbaFromHex(meta.color, 0.15);
    const border = rgbaFromHex(meta.color, 0.35);
    const style = bg ? `background:${bg}; color:${meta.color}; border:1px solid ${border};` : '';
    const cls = meta.key ? `category-${meta.key}` : '';
    const sAttr = style ? ` style="${style}"` : '';
    return `<span class="category-badge ${cls}"${sAttr}>${meta.label}</span>`;
}

function getSortedDecades() {
    const set = new Set();
    (eventsData.events || []).forEach(ev => {
        if (!ev || typeof ev !== 'object') return;
        const d = String(ev.decade || '').trim();
        if (d) set.add(d);
        const dy = decadeFromYear(ev.year);
        if (dy) set.add(dy);
    });
    const out = Array.from(set).filter(Boolean);
    out.sort((a, b) => {
        const na = parseInt(a, 10);
        const nb = parseInt(b, 10);
        if (!Number.isNaN(na) && !Number.isNaN(nb) && na !== nb) return na - nb;
        return String(a).localeCompare(String(b));
    });
    return out;
}

// Country normalization index (built from admin/country_mappings.js)
let _countryIndexCache = null;

function normalizeLookupKey(value) {
    if (value === null || value === undefined) return '';
    let s = String(value).trim();
    // Normalize curly apostrophes/quotes to ASCII
    s = s.replace(/[\u2019\u2018\u201B\u02BC’‘]/g, "'");
    s = s.replace(/\s+/g, ' ');
    // Remove combining marks then lowercase for robust matching
    // (e.g., Turkish dotted i can become i + combining dot above)
    s = s.normalize('NFKD').replace(/[\u0300-\u036f]/g, '');
    s = s.toLowerCase();
    // Dotless i
    s = s.replace(/ı/g, 'i');
    return s;
}

function getCountryIndex() {
    if (_countryIndexCache) return _countryIndexCache;

    const mappings = Array.isArray(window.__COUNTRY_MAPPINGS__) ? window.__COUNTRY_MAPPINGS__ : [];
    const lookup = new Map(); // normalized key -> { turkish, iso2 }
    const byTurkish = new Map(); // exact Turkish -> { turkish, iso2 }

    mappings.forEach(m => {
        const tr = (m.turkish || '').trim();
        const iso2 = (m.iso2 || '').trim().toUpperCase();
        if (!tr) return;
        const canon = { turkish: tr, iso2 };
        byTurkish.set(tr, canon);

        const keys = [m.turkish, m.english].concat(m.aliases || []);
        keys.forEach(k => {
            if (!k) return;
            const nk = normalizeLookupKey(k);
            if (!nk) return;
            if (!lookup.has(nk)) lookup.set(nk, canon);
        });
    });

    _countryIndexCache = { lookup, byTurkish, mappings };
    return _countryIndexCache;
}

function canonicalizeCountry(name) {
    const raw = (name || '').trim();
    if (!raw) return null;
    const idx = getCountryIndex();
    const hit = idx.lookup.get(normalizeLookupKey(raw));
    if (hit) return hit;
    return idx.byTurkish.get(raw) || null;
}

function eventRank(e) {
    const id = String(e.id || '');
    const isGap = id.startsWith('ev_gap_') ? 1 : 0;
    const lat = Number(e.lat || 0);
    const lon = Number(e.lon || 0);
    const hasCoords = (lat !== 0 || lon !== 0) ? 1 : 0;
    const wiki = String(e.wikipedia_url || '').trim();
    const hasWiki = wiki ? 1 : 0;
    const desc = String(e.description || '').trim();
    const descLen = desc.length;
    const hasCasualties = (e.casualties !== null && e.casualties !== undefined) ? 1 : 0;
    const kfLen = Array.isArray(e.key_figures) ? e.key_figures.length : 0;
    return [
        1 - isGap,
        hasCoords,
        hasWiki,
        descLen,
        hasCasualties,
        kfLen,
        id
    ];
}

function isBetterRank(a, b) {
    const n = Math.max(a.length, b.length);
    for (let i = 0; i < n; i++) {
        if (a[i] === b[i]) continue;
        return a[i] > b[i];
    }
    return false;
}

function mergeEventFields(target, source) {
    let changed = false;

    const tWiki = String(target.wikipedia_url || '').trim();
    const sWiki = String(source.wikipedia_url || '').trim();
    if (!tWiki && sWiki) {
        target.wikipedia_url = sWiki;
        changed = true;
    }

    const tDesc = String(target.description || '').trim();
    const sDesc = String(source.description || '').trim();
    if (!tDesc && sDesc) {
        target.description = sDesc;
        changed = true;
    } else if (sDesc.length > tDesc.length && sDesc !== tDesc) {
        target.description = sDesc;
        changed = true;
    }

    const tLat = Number(target.lat || 0);
    const tLon = Number(target.lon || 0);
    const sLat = Number(source.lat || 0);
    const sLon = Number(source.lon || 0);
    if ((tLat === 0 && tLon === 0) && (sLat !== 0 || sLon !== 0)) {
        target.lat = sLat;
        target.lon = sLon;
        changed = true;
    }

    const tCode = String(target.country_code || '').trim();
    const sCode = String(source.country_code || '').trim();
    if (!tCode && sCode) {
        target.country_code = sCode;
        changed = true;
    }

    if ((target.casualties === null || target.casualties === undefined) && (source.casualties !== null && source.casualties !== undefined)) {
        target.casualties = source.casualties;
        changed = true;
    }

    const tKf = Array.isArray(target.key_figures) ? target.key_figures : [];
    const sKf = Array.isArray(source.key_figures) ? source.key_figures : [];
    if (tKf.length || sKf.length) {
        const seen = new Set();
        const merged = [];
        [...tKf, ...sKf].forEach(x => {
            const v = String(x || '').trim();
            if (!v || seen.has(v)) return;
            seen.add(v);
            merged.push(v);
        });
        if (merged.join('|') !== tKf.map(x => String(x || '').trim()).join('|')) {
            target.key_figures = merged;
            changed = true;
        }
    }

    return changed;
}

function normalizeEventsDataInPlace() {
    const idx = getCountryIndex();
    let changedCountries = 0;
    let filledCodes = 0;
    let standardizedCodes = 0;
    let fixedDecades = 0;

    (eventsData.events || []).forEach(ev => {
        if (!ev || typeof ev !== 'object') return;
        const rawName = String(ev.country_name || '').trim();
        const canon = canonicalizeCountry(rawName);
        if (canon && canon.turkish && canon.turkish !== rawName) {
            ev.country_name = canon.turkish;
            changedCountries += 1;
        }

        const rawCode = String(ev.country_code || '').trim();
        const iso2 = canon && canon.iso2 ? canon.iso2.toUpperCase() : '';
        if (iso2) {
            if (!rawCode) {
                ev.country_code = iso2;
                filledCodes += 1;
            } else if (rawCode.toUpperCase() !== rawCode) {
                ev.country_code = rawCode.toUpperCase();
                standardizedCodes += 1;
            }
        } else if (rawCode && rawCode.toUpperCase() !== rawCode) {
            ev.country_code = rawCode.toUpperCase();
            standardizedCodes += 1;
        }

        // Keep decade aligned with year for both Admin + Map filters.
        const dy = decadeFromYear(ev.year);
        if (dy) {
            const rawDecade = String(ev.decade || '').trim();
            if (!rawDecade || rawDecade !== dy) {
                ev.decade = dy;
                fixedDecades += 1;
            }
        }
    });

    ensureCategoryDefsInPlace();

    // Dedupe: same country + year + title after normalization
    const byKey = new Map();
    const unique = [];
    let removed = 0;
    let mergedOps = 0;

    (eventsData.events || []).forEach(ev => {
        const c = String(ev.country_name || '').trim();
        const y = ev.year;
        const t = String(ev.title || '').trim();
        const key = `${c}||${y}||${t}`;
        const existing = byKey.get(key);
        if (!existing) {
            byKey.set(key, ev);
            unique.push(ev);
            return;
        }

        // Choose best as primary, then merge fields
        const existingRank = eventRank(existing);
        const evRank = eventRank(ev);
        let primary = existing;
        let secondary = ev;
        if (isBetterRank(evRank, existingRank)) {
            primary = ev;
            secondary = existing;
            // Replace in unique array
            const i = unique.indexOf(existing);
            if (i >= 0) unique[i] = ev;
            byKey.set(key, ev);
        }

        if (mergeEventFields(primary, secondary)) mergedOps += 1;
        removed += 1;
    });

    eventsData.events = unique;

    if (changedCountries || filledCodes || standardizedCodes || fixedDecades || removed) {
        console.log('Normalization applied:', { changedCountries, filledCodes, standardizedCodes, fixedDecades, removed, mergedOps });
    }
}

function populateCountryDatalist() {
    const list = document.getElementById('countryNameList');
    if (!list) return;
    list.innerHTML = '';

    const idx = getCountryIndex();
    const turkishNames = idx.mappings
        .map(m => (m.turkish || '').trim())
        .filter(Boolean)
        .sort((a, b) => a.localeCompare(b, 'tr'));

    turkishNames.forEach(name => {
        const option = document.createElement('option');
        option.value = name;
        list.appendChild(option);
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadData();
});

// Load data from localStorage or default
function loadData() {
    const stored = localStorage.getItem('geopoliticalEvents');
    if (stored) {
        eventsData = JSON.parse(stored);
    } else if (window.__EVENTS_DATA__) {
        eventsData = window.__EVENTS_DATA__;
    } else {
        // Try to load from file path (for local development)
        fetchDefaultData();
        return;
    }
    normalizeEventsDataInPlace();
    saveData();
    initializeUI();
}

// Fetch default data from events.json
async function fetchDefaultData() {
    try {
        const response = await fetch('../data/events.json');
        if (response.ok) {
            eventsData = await response.json();
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
    normalizeEventsDataInPlace();
    saveData();
    initializeUI();
}

// Save data to localStorage
function saveData() {
    localStorage.setItem('geopoliticalEvents', JSON.stringify(eventsData));
}

// Initialize UI
function initializeUI() {
    populateCountryFilter();
    populateDecadeSelects();
    populateCategorySelects();
    populateCountryDatalist();
    applyFilters();
    updateStats();
}

// Populate country filter dropdown
function populateCountryFilter() {
    const countries = [...new Set((eventsData.events || []).map(e => e.country_name).filter(Boolean))]
        .sort((a, b) => a.localeCompare(b, 'tr'));
    const select = document.getElementById('filterCountry');
    select.innerHTML = '<option value="">Tumu</option>';
    countries.forEach(country => {
        const option = document.createElement('option');
        option.value = country;
        option.textContent = country;
        select.appendChild(option);
    });
}

function populateDecadeSelects() {
    const decades = getSortedDecades();
    const filterSel = document.getElementById('filterDecade');
    const eventSel = document.getElementById('eventDecade');

    const prevFilter = filterSel ? String(filterSel.value || '') : '';
    const prevEvent = eventSel ? String(eventSel.value || '') : '';

    if (filterSel) {
        filterSel.innerHTML = '';
        ensureSelectHasOption(filterSel, '', 'Tumu');
        decades.forEach(d => ensureSelectHasOption(filterSel, d, d));
        filterSel.value = prevFilter;
    }

    if (eventSel) {
        eventSel.innerHTML = '';
        ensureSelectHasOption(eventSel, '', 'Secin');
        decades.forEach(d => ensureSelectHasOption(eventSel, d, d));
        eventSel.value = prevEvent;
    }
}

function populateCategorySelects() {
    ensureCategoryDefsInPlace();
    const defs = (eventsData && eventsData.categories) ? eventsData.categories : {};
    const cats = Object.keys(defs).map(k => getCategoryMeta(k));
    cats.sort((a, b) => String(a.label).localeCompare(String(b.label), 'tr'));

    const filterSel = document.getElementById('filterCategory');
    const eventSel = document.getElementById('eventCategory');

    const prevFilter = filterSel ? String(filterSel.value || '') : '';
    const prevEvent = eventSel ? String(eventSel.value || '') : '';

    if (filterSel) {
        filterSel.innerHTML = '';
        ensureSelectHasOption(filterSel, '', 'Tumu');
        cats.forEach(c => ensureSelectHasOption(filterSel, c.key, c.label));
        filterSel.value = prevFilter;
    }

    if (eventSel) {
        eventSel.innerHTML = '';
        ensureSelectHasOption(eventSel, '', 'Secin');
        cats.forEach(c => ensureSelectHasOption(eventSel, c.key, c.label));
        eventSel.value = prevEvent;
    }
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
            <td>${renderCategoryBadge(event.category)}</td>
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

    const rawCountryName = document.getElementById('countryName').value;
    const canon = canonicalizeCountry(rawCountryName);
    const countryName = canon ? canon.turkish : String(rawCountryName || '').trim();

    const rawCountryCode = document.getElementById('countryCode').value;
    const countryCode = (canon && canon.iso2) ? canon.iso2.toUpperCase() : String(rawCountryCode || '').toUpperCase();

    const eventData = {
        id: id || generateId(),
        country_code: countryCode,
        country_name: countryName,
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

    // Ensure we don't reintroduce duplicates or mixed country naming.
    normalizeEventsDataInPlace();
    saveData();
    closeModal();
    populateCountryFilter();
    populateDecadeSelects();
    populateCategorySelects();
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
    populateDecadeSelects();
    populateCategorySelects();
    applyFilters();
    updateStats();
}

// Reset localStorage state to the repo-embedded data (admin/data.js) or to ../data/events.json.
async function resetToRepoData() {
    const ok = confirm("Repo verisi tekrar yüklenecek. Local degisiklikleriniz kaybolabilir. Devam edilsin mi?");
    if (!ok) return;

    if (window.__EVENTS_DATA__) {
        // Deep copy so we don't mutate the embedded object reference.
        eventsData = JSON.parse(JSON.stringify(window.__EVENTS_DATA__));
        normalizeEventsDataInPlace();
        saveData();
        initializeUI();
        alert("Repo verisi yüklendi!");
        return;
    }

    try {
        const response = await fetch('../data/events.json', { cache: 'no-store' });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        eventsData = await response.json();
        normalizeEventsDataInPlace();
        saveData();
        initializeUI();
        alert("Repo verisi yüklendi!");
    } catch (e) {
        alert("Repo verisi yüklenemedi: " + (e && e.message ? e.message : String(e)));
    }
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
                normalizeEventsDataInPlace();
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
    const year = parseInt(this.value, 10);
    if (!Number.isFinite(year)) return;
    const decade = decadeFromYear(year);
    if (!decade) return;
    const sel = document.getElementById('eventDecade');
    if (!sel) return;
    ensureSelectHasOption(sel, decade, decade);
    sel.value = decade;
});

// Auto-canonicalize country name + fill ISO2 code from mappings
document.getElementById('countryName')?.addEventListener('change', function() {
    const canon = canonicalizeCountry(this.value);
    if (canon) {
        this.value = canon.turkish;
        const codeInput = document.getElementById('countryCode');
        if (codeInput && canon.iso2) codeInput.value = canon.iso2.toUpperCase();
    } else {
        this.value = String(this.value || '').trim();
    }
});
