document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const urlInput = document.getElementById('urlInput');
    const btnPaste = document.getElementById('btnPaste');
    const btnGenerate = document.getElementById('btnGenerate');
    const btnSpinner = document.getElementById('btnSpinner');
    const btnInstallApp = document.getElementById('btnInstallApp');
    
    const templateCards = document.querySelectorAll('.template-card');
    let selectedTemplate = 'economic';

    const progressCard = document.getElementById('progressCard');
    const progressBarFill = document.getElementById('progressBarFill');
    const progressPercent = document.getElementById('progressPercent');
    const progressTitle = document.getElementById('progressTitle');
    const steps = [
        document.getElementById('step1'),
        document.getElementById('step2'),
        document.getElementById('step3'),
        document.getElementById('step4')
    ];

    const resultCard = document.getElementById('resultCard');
    const resultTitle = document.getElementById('resultTitle');
    const resultSubtitle = document.getElementById('resultSubtitle');
    const btnDownloadPDF = document.getElementById('btnDownloadPDF');
    const btnPreviewPDF = document.getElementById('btnPreviewPDF');

    const previewModal = document.getElementById('previewModal');
    const btnCloseModal = document.getElementById('btnCloseModal');
    const pdfPreviewIframe = document.getElementById('pdfPreviewIframe');
    const modalPDFTitle = document.getElementById('modalPDFTitle');

    const historyGrid = document.getElementById('historyGrid');
    const btnRefreshHistory = document.getElementById('btnRefreshHistory');

    let currentPDFUrl = '';
    let deferredInstallPrompt = null;

    // Register Service Worker for PWA / Mobile Install
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js')
            .then(reg => console.log('PWA Service Worker registered:', reg.scope))
            .catch(err => console.log('Service Worker registration failed:', err));
    }

    // Handle PWA Install Prompt
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredInstallPrompt = e;
        if (btnInstallApp) {
            btnInstallApp.classList.remove('hide');
        }
    });

    if (btnInstallApp) {
        btnInstallApp.addEventListener('click', async () => {
            if (deferredInstallPrompt) {
                deferredInstallPrompt.prompt();
                const { outcome } = await deferredInstallPrompt.userChoice;
                if (outcome === 'accepted') {
                    console.log('User accepted PWA installation');
                }
                deferredInstallPrompt = null;
            } else {
                alert('📲 To install this App on Android:\n\n1. Tap the 3 dots (⋮) in the top-right corner of Chrome.\n2. Tap "Add to Home screen" or "Install App".\n\nAndroid will place the app icon directly on your home screen!');
            }
        });
    }

    // Parse incoming URLs from Android Web Share Target or URL params (?url=... or ?text=...)
    const urlParams = new URLSearchParams(window.location.search);
    const sharedUrl = urlParams.get('url') || urlParams.get('text');
    if (sharedUrl) {
        // Extract http URL from text if needed
        const urlMatch = sharedUrl.match(/https?:\/\/[^\s]+/);
        if (urlMatch) {
            urlInput.value = urlMatch[0];
            // Auto trigger generation for shared link
            setTimeout(() => {
                btnGenerate.click();
            }, 600);
        }
    }

    // Template Selection
    templateCards.forEach(card => {
        card.addEventListener('click', () => {
            templateCards.forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            selectedTemplate = card.dataset.template;
        });
    });

    // Clipboard Paste Button
    btnPaste.addEventListener('click', async () => {
        try {
            const text = await navigator.clipboard.readText();
            if (text && text.startsWith('http')) {
                urlInput.value = text;
            } else {
                alert('No valid URL found in clipboard.');
            }
        } catch (err) {
            alert('Clipboard permission denied. Please paste manually.');
        }
    });

    // Progress Helper
    function updateProgress(stepIdx, percent, title) {
        progressBarFill.style.width = percent + '%';
        progressPercent.textContent = percent + '%';
        if (title) progressTitle.textContent = title;
        
        steps.forEach((step, idx) => {
            if (idx <= stepIdx) {
                step.classList.add('active');
            } else {
                step.classList.remove('active');
            }
        });
    }

    // Generate PDF Submit Event
    btnGenerate.addEventListener('click', async () => {
        const url = urlInput.value.trim();
        if (!url || !url.startsWith('http')) {
            alert('Please enter a valid article URL starting with http:// or https://');
            return;
        }

        btnGenerate.disabled = true;
        btnSpinner.classList.remove('hide');
        resultCard.classList.add('hide');
        progressCard.classList.remove('hide');

        updateProgress(0, 20, '1/4: Fetching Article DOM...');

        try {
            setTimeout(() => updateProgress(1, 45, '2/4: Cleaning Paywalls & Extracting Story...'), 1200);
            setTimeout(() => updateProgress(2, 75, '3/4: Rendering Editorial Template...'), 2500);

            const cookieInput = document.getElementById('cookieInput');
            const response = await fetch('/api/convert', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    url: url,
                    template_id: selectedTemplate,
                    cookie_header: cookieInput ? cookieInput.value.trim() : ''
                })
            });

            const data = await response.json();

            if (response.ok && data.status === 'success') {
                updateProgress(3, 100, '4/4: PDF Generated Successfully!');
                
                setTimeout(() => {
                    progressCard.classList.add('hide');
                    resultCard.classList.remove('hide');

                    const item = data.data;
                    resultTitle.textContent = item.title || 'PDF Generated!';
                    resultSubtitle.textContent = `Saved: ${item.filename} (${(item.filesize / 1024).toFixed(1)} KB)`;
                    
                    currentPDFUrl = item.download_url;
                    btnDownloadPDF.href = item.download_url;
                    btnDownloadPDF.download = item.filename;

                    loadHistory();
                }, 600);
            } else {
                alert(`Error: ${data.detail || 'Failed to convert article.'}`);
                progressCard.classList.add('hide');
            }
        } catch (err) {
            console.error('Fetch error:', err);
            alert('Server connection error. Make sure server is running.');
            progressCard.classList.add('hide');
        } finally {
            btnGenerate.disabled = false;
            btnSpinner.classList.add('hide');
        }
    });

    // Preview Modal Events
    btnPreviewPDF.addEventListener('click', () => {
        if (currentPDFUrl) {
            pdfPreviewIframe.src = currentPDFUrl;
            modalPDFTitle.textContent = resultTitle.textContent;
            previewModal.classList.remove('hide');
        }
    });

    btnCloseModal.addEventListener('click', () => {
        previewModal.classList.add('hide');
        pdfPreviewIframe.src = '';
    });

    previewModal.addEventListener('click', (e) => {
        if (e.target === previewModal) {
            previewModal.classList.add('hide');
            pdfPreviewIframe.src = '';
        }
    });

    // Fetch History
    async function loadHistory() {
        try {
            const res = await fetch('/api/history');
            const data = await res.json();

            if (res.ok && data.history) {
                renderHistory(data.history);
            }
        } catch (err) {
            console.error('Failed to load history:', err);
        }
    }

    function renderHistory(items) {
        if (items.length === 0) {
            historyGrid.innerHTML = '<p style="color: var(--text-muted); grid-column: 1/-1;">No converted PDFs yet.</p>';
            return;
        }

        historyGrid.innerHTML = items.map(item => `
            <div class="history-card">
                <div class="history-card-name">${item.filename}</div>
                <div class="history-card-meta">
                    <span>${(item.filesize / 1024).toFixed(1)} KB</span>
                    <span>${item.formatted_date}</span>
                </div>
                <a href="${item.download_url}" download class="history-card-btn">📥 Download PDF</a>
            </div>
        `).join('');
    }

    btnRefreshHistory.addEventListener('click', loadHistory);

    // Initial Load
    loadHistory();
});
