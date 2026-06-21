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

        // Charts — assigned to hidden elements for API compatibility
        document.getElementById('distribution-chart').src = data.chart || '';
        document.getElementById('severity-chart').src     = data.severity_chart || '';

        // Render insights dashboard from already-loaded data
        renderInsightsDashboard(data);

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

    // ── Insights Dashboard ────────────────────────────────────────────────────
    function renderInsightsDashboard(data) {
        const risks       = data.risks           || [];
        const obligations = data.obligations     || [];
        const financials  = data.financial_terms || [];
        const clauses     = data.clauses         || [];
        const complex     = data.complex_terms   || [];
        const metadata    = data.metadata        || '';

        function realCount(arr) {
            return arr.filter(x => x && !/no specific|no items|not identified/i.test(x)).length;
        }

        const riskCount       = realCount(risks);
        const obligationCount = realCount(obligations);
        const financialCount  = realCount(financials);
        const clauseCount     = realCount(clauses);
        const complexCount    = realCount(complex);

        // Count-up animation
        function animateCounter(elId, target) {
            const el = document.getElementById(elId);
            if (!el) return;
            const t0 = performance.now();
            const dur = 900;
            function tick(now) {
                const t    = Math.min((now - t0) / dur, 1);
                const ease = 1 - Math.pow(1 - t, 3);
                el.textContent = Math.round(ease * target);
                if (t < 1) requestAnimationFrame(tick);
            }
            requestAnimationFrame(tick);
        }

        animateCounter('stat-risks-count',       riskCount);
        animateCounter('stat-obligations-count', obligationCount);
        animateCounter('stat-financial-count',   financialCount);
        animateCounter('stat-clauses-count',     clauseCount);

        // Risk severity counts
        let highCount = 0, medCount = 0, lowCount = 0;
        risks.forEach(r => {
            const rl = r.toLowerCase();
            if (rl.includes('[high]'))        highCount++;
            else if (rl.includes('[medium]')) medCount++;
            else if (rl.includes('[low]'))    lowCount++;
        });

        // ── Contract Health Score ─────────────────────────────────────
        const score = Math.max(10, Math.min(100,
            100 - highCount * 15 - medCount * 7 - lowCount * 3));
        animateCounter('health-score-number', score);

        let scoreColor, scoreLabel, scoreDesc;
        if (score >= 80) {
            scoreColor = '#22c55e'; scoreLabel = 'GOOD';
            scoreDesc  = 'Low risk profile. Contract appears well-structured.';
        } else if (score >= 50) {
            scoreColor = '#f59e0b'; scoreLabel = 'FAIR';
            scoreDesc  = 'Moderate risk detected. Review flagged clauses carefully.';
        } else {
            scoreColor = '#ef4444'; scoreLabel = 'HIGH RISK';
            scoreDesc  = 'Multiple high-severity risks identified. Legal review recommended.';
        }

        document.getElementById('health-score-label').textContent = scoreLabel;
        document.getElementById('health-score-label').style.color = scoreColor;
        document.getElementById('health-score-desc').textContent  = scoreDesc;

        const arcFill = document.getElementById('health-arc-fill');
        arcFill.style.stroke = scoreColor;
        requestAnimationFrame(() => {
            arcFill.style.strokeDasharray = ((score / 100) * 314.16) + ' 314.16';
        });

        // ── Risk Donut Chart ──────────────────────────────────────────
        const donutSvg    = document.getElementById('risk-donut-svg');
        const donutCenter = document.getElementById('donut-center-count');
        const donutLegend = document.getElementById('donut-legend');
        const riskTotal   = highCount + medCount + lowCount;
        donutCenter.textContent = riskTotal;
        donutSvg.querySelectorAll('.donut-seg').forEach(s => s.remove());

        if (riskTotal > 0) {
            const C = 2 * Math.PI * 60;
            const segs = [
                { count: highCount, color: '#e07a5f', label: 'High' },
                { count: medCount,  color: '#f2cc8f', label: 'Medium' },
                { count: lowCount,  color: '#81b29a', label: 'Low' },
            ].filter(s => s.count > 0);

            let cum = 0;
            segs.forEach(seg => {
                const len = (seg.count / riskTotal) * C;
                const c   = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                c.setAttribute('class', 'donut-seg');
                c.setAttribute('cx', '80'); c.setAttribute('cy', '80'); c.setAttribute('r', '60');
                c.setAttribute('fill', 'none');
                c.setAttribute('stroke', seg.color); c.setAttribute('stroke-width', '22');
                c.setAttribute('stroke-dasharray', len + ' ' + (C - len));
                c.setAttribute('stroke-dashoffset', String(-cum));
                c.setAttribute('transform', 'rotate(-90 80 80)');
                donutSvg.appendChild(c);
                cum += len;
            });

            donutLegend.innerHTML = '';
            segs.forEach(seg => {
                const pct = Math.round((seg.count / riskTotal) * 100);
                const div = document.createElement('div');
                div.className = 'donut-legend-item';
                div.innerHTML = '<span class="donut-dot" style="background:' + seg.color + '"></span>'
                    + seg.label + ' <strong>' + pct + '%</strong>';
                donutLegend.appendChild(div);
            });
        } else {
            donutLegend.innerHTML = '<div style="color:#94a3b8;font-style:italic;font-size:0.82rem;text-align:center;">No risks identified.</div>';
        }

        // ── Clause Category Bar Chart ─────────────────────────────────
        const barBody = document.getElementById('clause-bar-body');
        barBody.innerHTML = '';

        const CAT_COLORS = {
            payment: '#6366f1', termination: '#e07a5f', liability: '#f2cc8f',
            insurance: '#81b29a', confidentiality: '#3d405b',
            'room rent': '#06b6d4', 'sub-limit': '#8b5cf6',
            exclusion: '#f43f5e', 'waiting period': '#f97316', 'co-pay': '#10b981',
        };

        const catCounts = {};
        clauses.forEach(c => {
            if (!c || /no specific|not identified/i.test(c)) return;
            const m   = c.match(/^\[([^\]]+)\]/);
            const cat = m ? m[1].toLowerCase() : 'other';
            catCounts[cat] = (catCounts[cat] || 0) + 1;
        });

        const sorted  = Object.entries(catCounts).sort((a, b) => b[1] - a[1]);
        const maxCat  = sorted.length ? sorted[0][1] : 1;

        if (!sorted.length) {
            barBody.innerHTML = '<div style="color:#94a3b8;font-style:italic;font-size:0.82rem;">No categorized clauses found.</div>';
        } else {
            sorted.forEach(([cat, cnt], i) => {
                const pct   = Math.round((cnt / maxCat) * 100);
                const color = CAT_COLORS[cat] || '#94a3b8';
                const label = cat.charAt(0).toUpperCase() + cat.slice(1);
                const row   = document.createElement('div');
                row.className = 'bar-row';
                row.innerHTML = '<div class="bar-label">' + label + '</div>'
                    + '<div class="bar-track"><div class="bar-fill" style="--bar-color:'
                    + color + ';transition-delay:' + (i * 0.1) + 's"></div></div>'
                    + '<div class="bar-count">' + cnt + '</div>';
                barBody.appendChild(row);
                requestAnimationFrame(() => requestAnimationFrame(() => {
                    const fill = row.querySelector('.bar-fill');
                    if (fill) fill.style.width = pct + '%';
                }));
            });
        }

        // ── Document Intelligence ─────────────────────────────────────
        const intelBody = document.getElementById('doc-intel-body');
        intelBody.innerHTML = '';

        const wcMatch    = metadata.match(/word count:\s*([\d,]+)/i);
        const wordCount  = wcMatch ? parseInt(wcMatch[1].replace(',', '')) : null;
        const chkMatch   = metadata.match(/chunks?:\s*(\d+)/i);
        const chunkCount = chkMatch ? parseInt(chkMatch[1]) : null;

        const totalItems = riskCount + obligationCount + financialCount + clauseCount + complexCount;
        let complexity, complexColor;
        if (totalItems > 20)      { complexity = 'High';   complexColor = '#e07a5f'; }
        else if (totalItems > 10) { complexity = 'Medium'; complexColor = '#f59e0b'; }
        else                      { complexity = 'Low';    complexColor = '#22c55e'; }

        const readMins = wordCount ? Math.ceil(wordCount / 150) : null;

        [
            wordCount  ? { icon: 'fa-file-lines',  label: 'Word Count',        value: wordCount.toLocaleString(), color: null }  : null,
            chunkCount ? { icon: 'fa-layer-group', label: 'Sections Analyzed', value: String(chunkCount),         color: null }  : null,
            { icon: 'fa-list-check', label: 'Total Findings', value: String(totalItems), color: null         },
            { icon: 'fa-gauge-high', label: 'Complexity',     value: complexity,          color: complexColor },
            readMins   ? { icon: 'fa-clock',       label: 'Est. Read Time',    value: '~' + readMins + ' min', color: null }  : null,
            { icon: 'fa-robot',      label: 'Analyzed By',    value: 'LegalLens AI Engine', color: '#6366f1' },
        ].filter(Boolean).forEach(m => {
            const item = document.createElement('div');
            item.className = 'doc-intel-item';
            item.innerHTML = '<div class="doc-intel-icon"><i class="fa-solid ' + m.icon + '"></i></div>'
                + '<div class="doc-intel-info">'
                + '<div class="doc-intel-label">' + m.label + '</div>'
                + '<div class="doc-intel-value"' + (m.color ? ' style="color:' + m.color + '"' : '') + '>'
                + m.value + '</div></div>';
            intelBody.appendChild(item);
        });

        // ── AI Key Insights ───────────────────────────────────────────
        const aiGrid = document.getElementById('ai-insights-grid');
        aiGrid.innerHTML = '';

        [
            highCount > 0       ? { icon: 'fa-circle-exclamation', color: '#e07a5f', title: highCount + ' High-Risk Clause' + (highCount > 1 ? 's' : ''),           desc: 'Immediate legal review recommended for these critical items.' } : null,
            obligationCount > 0 ? { icon: 'fa-clipboard-list',     color: '#6366f1', title: obligationCount + ' Obligation' + (obligationCount > 1 ? 's' : ''),     desc: 'Review all obligations to understand your contractual duties.' } : null,
            financialCount > 0  ? { icon: 'fa-sack-dollar',        color: '#81b29a', title: financialCount + ' Financial Term' + (financialCount > 1 ? 's' : ''),   desc: 'Financial commitments and payment structures identified.' } : null,
            clauseCount > 0     ? { icon: 'fa-file-contract',      color: '#3d405b', title: clauseCount + ' Clause' + (clauseCount > 1 ? 's' : '') + ' Categorized', desc: 'Organized by type for efficient review.' } : null,
            complexCount > 0    ? { icon: 'fa-book-open',          color: '#f59e0b', title: complexCount + ' Complex Term' + (complexCount > 1 ? 's' : ''),         desc: 'Legal jargon requiring specialist understanding.' } : null,
            { icon: 'fa-shield-halved', color: scoreColor,
              title: 'Health Score: ' + score + '/100',
              desc:  'Contract rated ' + scoreLabel.toLowerCase() + ' based on risk analysis.' },
        ].filter(Boolean).forEach((ins, i) => {
            const card = document.createElement('div');
            card.className = 'ai-insight-item';
            card.style.setProperty('--ins-color', ins.color);
            card.style.animationDelay = (i * 0.08) + 's';
            card.innerHTML = '<div class="ai-insight-icon" style="color:' + ins.color + '"><i class="fa-solid ' + ins.icon + '"></i></div>'
                + '<div class="ai-insight-text">'
                + '<div class="ai-insight-title">' + ins.title + '</div>'
                + '<div class="ai-insight-desc">'  + ins.desc  + '</div>'
                + '</div>';
            aiGrid.appendChild(card);
        });
    }

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
