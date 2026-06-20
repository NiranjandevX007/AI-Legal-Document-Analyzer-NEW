document.addEventListener('DOMContentLoaded', () => {
    // ── DOM refs ────────────────────────────────────────��─────────────────────
    const dropZone      = document.getElementById('drop-zone');
    const fileInput     = document.getElementById('file-input');
    const fileInfo      = document.getElementById('file-info');
    const fileName      = document.getElementById('file-name');
    const removeFileBtn = document.getElementById('remove-file');
    const analyzeBtn    = document.getElementById('analyze-btn');

    const initialView   = document.getElementById('initial-view');
    const uploadPanel   = document.getElementById('upload-panel');
    const loadingPanel  = document.getElementById('loading-panel');
    const appView       = document.getElementById('app-view');
    const newAnalysisBtn= document.getElementById('new-analysis-btn');
    const langEnBtn     = document.getElementById('lang-en-btn');
    const langKnBtn     = document.getElementById('lang-kn-btn');
    const langStatus    = document.getElementById('lang-status');

    // ── State ─────────────────────────────────────────────────────────────────
    let selectedFile  = null;
    let englishData   = null;
    let kannadaData   = null;
    let currentLang   = 'en';   // 'en' | 'kn'

    // ── Language label switching ──────────────────────────────────────────────
    /**
     * Swap every .nav-label span and every [data-en] page-title text node
     * to the requested language. Charts are never touched here.
     */
    function applyLanguageLabels(lang) {
        console.log('[lang] applyLanguageLabels called with:', lang);

        // 1. Nav labels (spans with data-en / data-kn)
        const navLabels = document.querySelectorAll('.nav-label');
        console.log('[lang] .nav-label elements found:', navLabels.length);
        navLabels.forEach(span => {
            span.textContent = span.getAttribute('data-' + lang) || span.getAttribute('data-en');
        });

        // 2. Page titles — each <h2> has data-en / data-kn and an <i> child icon
        const pageTitles = document.querySelectorAll('.page-title[data-en]');
        console.log('[lang] .page-title[data-en] elements found:', pageTitles.length);
        pageTitles.forEach(h2 => {
            const iconEl = h2.querySelector('i');          // preserve the icon
            const text   = h2.getAttribute('data-' + lang) || h2.getAttribute('data-en');
            h2.textContent = '';                           // clear everything
            if (iconEl) h2.appendChild(iconEl);           // re-add icon first
            h2.appendChild(document.createTextNode(' ' + text));
        });

        // 3. Active-state styling on lang buttons
        langEnBtn.classList.toggle('lang-active', lang === 'en');
        langKnBtn.classList.toggle('lang-active', lang === 'kn');

        currentLang = lang;
        console.log('[lang] currentLang is now:', currentLang);
    }

    // ── Drag-and-drop ─────────────────────────────────────────────────────────
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(evt => {
        dropZone.addEventListener(evt, e => { e.preventDefault(); e.stopPropagation(); }, false);
    });
    ['dragenter', 'dragover'].forEach(evt => {
        dropZone.addEventListener(evt, () => dropZone.classList.add('dragover'), false);
    });
    ['dragleave', 'drop'].forEach(evt => {
        dropZone.addEventListener(evt, () => dropZone.classList.remove('dragover'), false);
    });
    dropZone.addEventListener('drop', e => handleFiles(e.dataTransfer.files));
    fileInput.addEventListener('change', function () { handleFiles(this.files); });

    function handleFiles(files) {
        if (!files.length) return;
        const file = files[0];
        if (file.type === 'application/pdf') {
            selectedFile = file;
            fileName.textContent = file.name;
            dropZone.classList.add('hidden');
            fileInfo.classList.remove('hidden');
            analyzeBtn.classList.remove('hidden');
        } else {
            alert('Please upload a valid PDF file.');
        }
    }

    removeFileBtn.addEventListener('click', () => {
        selectedFile = null;
        fileInput.value = '';
        dropZone.classList.remove('hidden');
        fileInfo.classList.add('hidden');
        analyzeBtn.classList.add('hidden');
    });

    // ── Upload & Analyze ─────────────────────────────────────────────────────
    analyzeBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        uploadPanel.classList.add('hidden');
        loadingPanel.classList.remove('hidden');

        const formData = new FormData();
        formData.append('file', selectedFile);

        try {
            const response = await fetch('/upload', { method: 'POST', body: formData });
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Failed to process document');
            }
            const data = await response.json();
            englishData = data;
            displayResults(data);
        } catch (error) {
            alert('Error: ' + error.message);
            loadingPanel.classList.add('hidden');
            uploadPanel.classList.remove('hidden');
        }
    });

    // ── Display helpers ───────────────────────────────────────────────────────
    /**
     * Apply all text content to the DOM (content only, no charts, no panels).
     * Called on initial display and on every language switch.
     */
    function applyData(data) {
        if (data.metadata) {
            document.getElementById('metadata-text').textContent = data.metadata;
        }
        document.getElementById('summary-text').textContent = data.summary || '';
        populateList('complex-list',     data.complex_terms);
        populateList('risks-list',       data.risks);
        populateList('obligations-list', data.obligations);
        populateList('financial-list',   data.financial_terms);
        populateList('clauses-list',     data.clauses);
    }

    /**
     * First display after a successful upload.
     * Sets charts (once) and resets to EN labels + Summary page.
     */
    function displayResults(data) {
        initialView.classList.add('hidden');
        loadingPanel.classList.add('hidden');
        appView.classList.remove('hidden');

        applyData(data);

        // Charts — set once, untouched on language switches
        document.getElementById('distribution-chart').src = data.chart || '';
        const sevChart = document.getElementById('severity-chart');
        if (data.severity_chart) {
            sevChart.src = data.severity_chart;
            sevChart.style.display = 'block';
        } else {
            sevChart.style.display = 'none';
        }

        // Reset language to EN (new doc always starts in English)
        kannadaData = null;
        applyLanguageLabels('en');

        // Reset to Summary page
        document.querySelector('.nav-btn[data-page="page-summary"]').click();
    }

    function populateList(elementId, items) {
        const ul = document.getElementById(elementId);
        ul.innerHTML = '';

        const isEmpty = !items || items.length === 0 ||
            (items.length === 1 && /no specific|no items|not identified/i.test(items[0]));

        if (isEmpty) {
            ul.innerHTML = '<li style="border-left-color:transparent;color:#94a3b8;font-style:italic;">No items found in this category.</li>';
            return;
        }

        items.forEach(item => {
            if (!item || item.toLowerCase() === 'none') return;

            const li = document.createElement('li');
            let cleanText = item.replace(/^[\s\-]+|[\s\-]+$/g, '');
            if (!cleanText) return;

            // Capitalise first character (safe for Kannada — only affects ASCII range)
            if (/^[a-z]/.test(cleanText)) {
                cleanText = cleanText.charAt(0).toUpperCase() + cleanText.slice(1);
            }
            // Add trailing punctuation only for ASCII text
            if (/[a-zA-Z0-9]$/.test(cleanText)) {
                cleanText += '.';
            }

            // Extract [Badge] prefix
            const badgeMatch = cleanText.match(/^\[([^\]]+)\]\s*([\s\S]*)/);
            if (badgeMatch) {
                const badgeText = badgeMatch[1].trim();
                const rest      = badgeMatch[2];

                if (elementId === 'risks-list') {
                    li.setAttribute('data-severity', badgeText.toLowerCase());
                }

                const badgeSpan = document.createElement('span');
                badgeSpan.className = 'badge badge-' + badgeText.toLowerCase().replace(/[^a-z0-9]/g, '-');
                badgeSpan.textContent = badgeText.toUpperCase();
                li.appendChild(badgeSpan);
                li.appendChild(document.createTextNode(' ' + rest));
            } else {
                li.textContent = cleanText;
            }

            ul.appendChild(li);
        });

        if (ul.children.length === 0) {
            ul.innerHTML = '<li style="border-left-color:transparent;color:#94a3b8;font-style:italic;">No items found in this category.</li>';
        }
    }

    // ── Risk filter buttons ───────────────────────────────────────────────────
    const riskFilterBtns = document.querySelectorAll('.risk-filter-btn');
    riskFilterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            riskFilterBtns.forEach(b => {
                b.classList.remove('active');
                b.style.backgroundColor = 'transparent';
                if (b.getAttribute('data-filter') !== 'all') {
                    b.style.color = b.style.borderColor;
                } else {
                    b.style.color = '';
                }
            });
            btn.classList.add('active');
            btn.style.backgroundColor = btn.style.borderColor || 'var(--primary-color)';
            btn.style.color = '#fff';

            const filter = btn.getAttribute('data-filter');
            document.querySelectorAll('#risks-list li').forEach(li => {
                if (li.textContent.includes('No items found')) return;
                li.style.display = (filter === 'all' || li.getAttribute('data-severity') === filter)
                    ? 'list-item' : 'none';
            });
        });
    });

    // ── Page navigation ───────────────────────────────────────────────────────
    const navBtns      = document.querySelectorAll('.nav-btn');
    const pageSections = document.querySelectorAll('.page-section');

    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            navBtns.forEach(b => b.classList.remove('active'));
            pageSections.forEach(p => { p.classList.remove('active'); });

            btn.classList.add('active');

            const targetId   = btn.getAttribute('data-page');
            const targetPage = document.getElementById(targetId);
            targetPage.classList.remove('hidden');
            targetPage.style.display = 'block';
            setTimeout(() => targetPage.classList.add('active'), 10);

            pageSections.forEach(p => {
                if (p.id !== targetId) {
                    p.style.display = 'none';
                    p.classList.add('hidden');
                }
            });

            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    });

    // ── Language buttons ──────────────────────────────────────────────────────
    langKnBtn.addEventListener('click', async () => {
        if (!englishData) return;
        if (currentLang === 'kn') return;   // already in Kannada

        // Cache hit — just re-apply
        if (kannadaData) {
            applyData(kannadaData);
            applyLanguageLabels('kn');
            return;
        }

        // Show loading state, disable both buttons
        langEnBtn.disabled = true;
        langKnBtn.disabled = true;
        langStatus.classList.remove('hidden');

        try {
            const response = await fetch('/translate-kannada', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    summary:        englishData.summary        || '',
                    metadata:       englishData.metadata       || '',
                    complex_terms:  englishData.complex_terms  || [],
                    risks:          englishData.risks          || [],
                    obligations:    englishData.obligations    || [],
                    financial_terms:englishData.financial_terms|| [],
                    clauses:        englishData.clauses        || [],
                })
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Translation failed');
            }

            kannadaData = await response.json();
            applyData(kannadaData);
            applyLanguageLabels('kn');

        } catch (error) {
            alert('Translation error: ' + error.message);
        } finally {
            langEnBtn.disabled = false;
            langKnBtn.disabled = false;
            langStatus.classList.add('hidden');
        }
    });

    langEnBtn.addEventListener('click', () => {
        if (!englishData) return;
        if (currentLang === 'en') return;   // already in English
        applyData(englishData);
        applyLanguageLabels('en');
    });

    // ── New Analysis ──────────────────────────────────────────────────────────
    newAnalysisBtn.addEventListener('click', () => {
        // Reset state
        englishData = null;
        kannadaData = null;

        // Reset UI labels back to English
        applyLanguageLabels('en');

        appView.classList.add('hidden');
        initialView.classList.remove('hidden');
        uploadPanel.classList.remove('hidden');
        removeFileBtn.click();
    });
});
