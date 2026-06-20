document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const fileInfo = document.getElementById('file-info');
    const fileName = document.getElementById('file-name');
    const removeFileBtn = document.getElementById('remove-file');
    const analyzeBtn = document.getElementById('analyze-btn');
    
    // View containers
    const initialView = document.getElementById('initial-view');
    const uploadPanel = document.getElementById('upload-panel');
    const loadingPanel = document.getElementById('loading-panel');
    const appView = document.getElementById('app-view');
    const newAnalysisBtn = document.getElementById('new-analysis-btn');

    let selectedFile = null;
    let englishData = null;
    let kannadaData = null;
    // Drag and Drop Events
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.remove('dragover');
        }, false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    });

    fileInput.addEventListener('change', function() {
        handleFiles(this.files);
    });

    function handleFiles(files) {
        if (files.length > 0) {
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
    }

    removeFileBtn.addEventListener('click', () => {
        selectedFile = null;
        fileInput.value = '';
        dropZone.classList.remove('hidden');
        fileInfo.classList.add('hidden');
        analyzeBtn.classList.add('hidden');
    });

    analyzeBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        uploadPanel.classList.add('hidden');
        loadingPanel.classList.remove('hidden');

        const formData = new FormData();
        formData.append('file', selectedFile);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to process document');
            }

            displayResults(data);
           const data = await response.json();

           englishData = data;

           displayResults(data);

        } catch (error) {
            alert('Error: ' + error.message);
            loadingPanel.classList.add('hidden');
            uploadPanel.classList.remove('hidden');
        }
    });

    function displayResults(data) {
        // Hide the initial container, show the full app view
        initialView.classList.add('hidden');
        loadingPanel.classList.add('hidden');
        appView.classList.remove('hidden');

        // Populate Metadata Banner
        if(data.metadata) {
            document.getElementById('metadata-text').textContent = data.metadata;
        }

        // Populate Summary
        document.getElementById('summary-text').textContent = data.summary;
        
        // Populate Chart
        document.getElementById('distribution-chart').src = data.chart;
        if(data.severity_chart) {
            document.getElementById('severity-chart').src = data.severity_chart;
            document.getElementById('severity-chart').style.display = 'block';
        } else {
            document.getElementById('severity-chart').style.display = 'none';
        }

        // Populate Lists with minor text cleanup
        populateList('complex-list', data.complex_terms);
        populateList('risks-list', data.risks);
        populateList('obligations-list', data.obligations);
        populateList('financial-list', data.financial_terms);
        populateList('clauses-list', data.clauses);

        
        // Reset to first page
        document.querySelector('.nav-btn[data-page="page-summary"]').click();
    }

    function populateList(elementId, items) {
        const ul = document.getElementById(elementId);
        ul.innerHTML = '';
        if (!items || items.length === 0 || (items.length === 1 && items[0].includes("No specific"))) {
            ul.innerHTML = '<li style="border-left-color: transparent; color: #94a3b8; font-style: italic;">No items found in this category.</li>';
            return;
        }
        
        items.forEach(item => {
            if (item.toLowerCase() === 'none') return; // Skip literal "None"
            
            const li = document.createElement('li');
            
            // Minor text cleaning: ensure capital letter start and punctuation end
            let cleanText = item.replace(/^[\s-]+|[\s-]+$/g, '');
            if (cleanText.length > 0) {
                cleanText = cleanText.charAt(0).toUpperCase() + cleanText.slice(1);
                if (!['.', '!', '?'].includes(cleanText.slice(-1))) {
                    cleanText += '.';
                }
            }
            
            // Extract [Category] or [Severity] badges
            const badgeMatch = cleanText.match(/^\[(.*?)\]\s*(.*)/);
            if (badgeMatch) {
                const badgeText = badgeMatch[1];
                cleanText = badgeMatch[2];
                
                if(elementId === 'risks-list') {
                    li.setAttribute('data-severity', badgeText.toLowerCase().trim());
                }
                
                const badgeSpan = document.createElement('span');
                badgeSpan.className = 'badge badge-' + badgeText.toLowerCase().replace(/[^a-z0-9]/g, '-');
                badgeSpan.textContent = badgeText.toUpperCase();
                li.appendChild(badgeSpan);
                li.appendChild(document.createTextNode(' ' + cleanText));
            } else {
                li.textContent = cleanText;
            }
            
            ul.appendChild(li);
        });
        
        // If everything was skipped
        if(ul.children.length === 0) {
            ul.innerHTML = '<li style="border-left-color: transparent; color: #94a3b8; font-style: italic;">No items found in this category.</li>';
        }
    }

    // Risk Filtering Logic
    const riskFilterBtns = document.querySelectorAll('.risk-filter-btn');
    riskFilterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            riskFilterBtns.forEach(b => {
                b.classList.remove('active');
                b.style.backgroundColor = 'transparent';
            });
            btn.classList.add('active');
            
            // Highlight active button with its border color
            btn.style.backgroundColor = btn.style.borderColor;
            btn.style.color = '#fff';
            
            // Reset other buttons text color
            riskFilterBtns.forEach(b => {
                if(!b.classList.contains('active') && b.getAttribute('data-filter') !== 'all') {
                    b.style.color = b.style.borderColor;
                } else if(!b.classList.contains('active')) {
                    b.style.color = ''; // reset All button
                }
            });
            
            const filter = btn.getAttribute('data-filter');
            const risks = document.querySelectorAll('#risks-list li');
            
            risks.forEach(li => {
                if(li.textContent.includes('No items found')) return;
                
                if(filter === 'all') {
                    li.style.display = 'list-item';
                } else {
                    if(li.getAttribute('data-severity') === filter) {
                        li.style.display = 'list-item';
                    } else {
                        li.style.display = 'none';
                    }
                }
            });
        });
    });

    // Full-Page Navigation Logic with Smooth Transitions
    const navBtns = document.querySelectorAll('.nav-btn');
    const pageSections = document.querySelectorAll('.page-section');

    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all buttons and pages
            navBtns.forEach(b => b.classList.remove('active'));
            pageSections.forEach(p => p.classList.remove('active'));

            // Add active class to clicked button
            btn.classList.add('active');

            // Show target page
            const targetId = btn.getAttribute('data-page');
            const targetPage = document.getElementById(targetId);
            
            // Slight delay hack to trigger CSS transition properly if display was none
            targetPage.classList.remove('hidden');
            targetPage.style.display = 'block';
            setTimeout(() => {
                targetPage.classList.add('active');
            }, 10);
            
            // Hide other pages
            pageSections.forEach(p => {
                if (p.id !== targetId) {
                    p.style.display = 'none';
                    p.classList.add('hidden');
                }
            });
            
            // Scroll to top of the content area smoothly
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    });

    newAnalysisBtn.addEventListener('click', () => {
        // Return to upload screen
        appView.classList.add('hidden');
        initialView.classList.remove('hidden');
        uploadPanel.classList.remove('hidden');
        removeFileBtn.click();
    });
});
