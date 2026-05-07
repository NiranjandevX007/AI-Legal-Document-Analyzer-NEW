document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const fileInfo = document.getElementById('file-info');
    const fileName = document.getElementById('file-name');
    const removeFileBtn = document.getElementById('remove-file');
    const analyzeBtn = document.getElementById('analyze-btn');
    const uploadPanel = document.getElementById('upload-panel');
    const loadingPanel = document.getElementById('loading-panel');
    const resultsPanel = document.getElementById('results-panel');
    const newAnalysisBtn = document.getElementById('new-analysis-btn');

    let selectedFile = null;

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

            const data = await response.json();
            displayResults(data);
        } catch (error) {
            alert('Error: ' + error.message);
            loadingPanel.classList.add('hidden');
            uploadPanel.classList.remove('hidden');
        }
    });

    function displayResults(data) {
        loadingPanel.classList.add('hidden');
        resultsPanel.classList.remove('hidden');

        document.getElementById('summary-text').textContent = data.summary;
        document.getElementById('distribution-chart').src = data.chart;

        populateList('complex-list', data.complex_terms);
        populateList('risks-list', data.risks);
        populateList('obligations-list', data.obligations);
        populateList('financial-list', data.financial_terms);
    }

    function populateList(elementId, items) {
        const ul = document.getElementById(elementId);
        ul.innerHTML = '';
        if (!items || items.length === 0) {
            ul.innerHTML = '<li>No items found in this category.</li>';
            return;
        }
        items.forEach(item => {
            const li = document.createElement('li');
            li.textContent = item.replace(/^[\s-]+|[\s-]+$/g, ''); // Basic clean
            ul.appendChild(li);
        });
    }

    newAnalysisBtn.addEventListener('click', () => {
        resultsPanel.classList.add('hidden');
        removeFileBtn.click();
        uploadPanel.classList.remove('hidden');
    });
});
