document.addEventListener('DOMContentLoaded', async () => {
    const tabUrlDiv = document.getElementById('tabUrl');
    const templateSelect = document.getElementById('templateSelect');
    const btnConvert = document.getElementById('btnConvert');
    const statusMsg = document.getElementById('statusMsg');

    let activeUrl = '';
    let activeTabId = null;

    // Query active tab URL
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (tab && tab.url) {
            activeUrl = tab.url;
            activeTabId = tab.id;
            tabUrlDiv.textContent = activeUrl;
        }
    } catch (e) {
        tabUrlDiv.textContent = 'Could not detect active tab.';
    }

    btnConvert.addEventListener('click', async () => {
        if (!activeUrl || !activeUrl.startsWith('http')) {
            showStatus('Invalid tab URL. Must be an http/https link.', 'error');
            return;
        }

        showStatus('⏳ Extracting page DOM & converting to PDF...', 'loading');
        btnConvert.disabled = true;

        let rawHtml = '';
        try {
            // Extract exact DOM outerHTML from active browser tab
            const [{ result }] = await chrome.scripting.executeScript({
                target: { tabId: activeTabId },
                func: () => document.documentElement.outerHTML
            });
            rawHtml = result || '';
        } catch (e) {
            console.log('Script execution warning:', e);
        }

        try {
            const response = await fetch('http://localhost:8000/api/convert', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    url: activeUrl,
                    template_id: templateSelect.value,
                    raw_html: rawHtml
                })
            });

            const data = await response.json();

            if (response.ok && data.status === 'success') {
                showStatus('✨ PDF Created! Downloading...', 'success');
                
                const pdfDownloadUrl = `http://localhost:8000${data.data.download_url}`;
                window.open(pdfDownloadUrl, '_blank');
            } else {
                showStatus(`Error: ${data.detail || 'Failed to convert'}`, 'error');
            }
        } catch (err) {
            showStatus('Error connecting to local server at http://localhost:8000', 'error');
        } finally {
            btnConvert.disabled = false;
        }
    });

    function showStatus(text, type) {
        statusMsg.textContent = text;
        statusMsg.className = `status ${type}`;
        statusMsg.style.display = 'block';
    }
});
