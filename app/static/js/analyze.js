/**
 * analyze.js — Client-side interaction logic for the Analyze Job page
 * Following docs/02_UI_UX_SPEC.md (sections 7.1, 7.2, 7.3, 7.4) and prompts P9 & P10:
 * - Tabs: Text | Image | Link
 * - Camera getUserMedia with facingMode environment, capture, switch, retake
 * - Device file picker & drag-and-drop zone
 * - In-memory image preview & scanning laser animation
 * - OCR extraction via POST /api/ocr
 * - Live word counters & clear buttons
 * - Segmented model selector (Logistic Regression / Random Forest)
 * - Temporary result block with explainability chips and flags
 */

document.addEventListener('DOMContentLoaded', () => {
  // --- DOM Elements ---
  const tabBtnText = document.getElementById('tab-btn-text');
  const tabBtnImage = document.getElementById('tab-btn-image');
  const tabBtnLink = document.getElementById('tab-btn-link');
  const tabPanelText = document.getElementById('tab-panel-text');
  const tabPanelImage = document.getElementById('tab-panel-image');
  const tabPanelLink = document.getElementById('tab-panel-link');

  // Text Tab
  const textInput = document.getElementById('job-text-input');
  const clearTextBtn = document.getElementById('clear-text-btn');
  const wordCounter = document.getElementById('word-counter');
  const wordValidationMsg = document.getElementById('word-validation-msg');

  // Image Tab
  const openCameraBtn = document.getElementById('open-camera-btn');
  const importDeviceBtn = document.getElementById('import-device-btn');
  const imageFileInput = document.getElementById('image-file-input');
  const imageDropzone = document.getElementById('image-dropzone');
  const cameraErrorAlert = document.getElementById('camera-error-alert');
  const cameraPreviewContainer = document.getElementById('camera-preview-container');
  const cameraVideo = document.getElementById('camera-video');
  const cameraCanvas = document.getElementById('camera-canvas');
  const cameraCaptureBtn = document.getElementById('camera-capture-btn');
  const cameraSwitchBtn = document.getElementById('camera-switch-btn');
  const cameraCancelBtn = document.getElementById('camera-cancel-btn');

  const imageScanningContainer = document.getElementById('image-scanning-container');
  const ocrPreviewImg = document.getElementById('ocr-preview-img');
  const ocrLaser = document.getElementById('ocr-laser');
  const ocrStatusMsg = document.getElementById('ocr-status-msg');
  const ocrErrorAlert = document.getElementById('ocr-error-alert');
  const ocrErrorText = document.getElementById('ocr-error-text');
  const ocrResultContainer = document.getElementById('ocr-result-container');
  const ocrExtractedTextarea = document.getElementById('ocr-extracted-textarea');
  const ocrRetakeBtn = document.getElementById('ocr-retake-btn');
  const ocrWordCounter = document.getElementById('ocr-word-counter');

  // Link Tab
  const urlInput = document.getElementById('job-url-input');
  const fetchUrlBtn = document.getElementById('fetch-url-btn');
  const fetchBtnSpinner = document.getElementById('fetch-btn-spinner');
  const fetchBtnText = document.getElementById('fetch-btn-text');
  const fetchErrorBox = document.getElementById('fetch-error-box');
  const fetchedContainer = document.getElementById('fetched-text-container');
  const fetchedTextArea = document.getElementById('fetched-text-area');
  const fetchedWordCounter = document.getElementById('fetched-word-counter');

  // Controls & Actions
  const modelBtnLr = document.getElementById('model-btn-lr');
  const modelBtnRf = document.getElementById('model-btn-rf');
  const analyzeBtn = document.getElementById('analyze-btn');
  const analyzeSpinner = document.getElementById('analyze-spinner');
  const analyzeIcon = document.getElementById('analyze-icon');
  const analyzeText = document.getElementById('analyze-text');
  const analyzeErrorAlert = document.getElementById('analyze-error-alert');
  const analyzeErrorMsg = document.getElementById('analyze-error-msg');

  // Result Elements
  const tempResultBlock = document.getElementById('temp-result-block');
  const verdictIconContainer = document.getElementById('verdict-icon-container');
  const verdictBadge = document.getElementById('verdict-badge');
  const verdictSubtitle = document.getElementById('verdict-subtitle');
  const resultProbability = document.getElementById('result-probability');
  const resultThreshold = document.getElementById('result-threshold');
  const resultModelName = document.getElementById('result-model-name');
  const resultFlagsContainer = document.getElementById('result-flags-container');
  const resultFlagsList = document.getElementById('result-flags-list');
  const resultFakeWords = document.getElementById('result-fake-words');
  const resultRealWords = document.getElementById('result-real-words');
  const resultHighlightedText = document.getElementById('result-highlighted-text');
  const viewFullResultLink = document.getElementById('view-full-result-link');

  // Internal State
  let activeTab = 'text';
  let selectedModel = 'lr';
  let currentCameraStream = null;
  let currentFacingMode = 'environment'; // Rear camera first

  // --- Helper: Count words ---
  function countWords(str) {
    if (!str || !str.trim()) return 0;
    return str.trim().split(/\s+/).length;
  }

  // --- 1. Tab Navigation & Camera Cleanup ---
  function stopCamera() {
    if (currentCameraStream) {
      currentCameraStream.getTracks().forEach(track => track.stop());
      currentCameraStream = null;
    }
    if (cameraPreviewContainer) {
      cameraPreviewContainer.style.display = 'none';
    }
    if (imageDropzone && !imageScanningContainer.style.display.includes('block') && !ocrResultContainer.style.display.includes('block')) {
      imageDropzone.style.display = 'flex';
    }
  }

  function setActiveTab(tab) {
    // Stop camera whenever leaving or switching tabs
    stopCamera();

    activeTab = tab;
    [tabBtnText, tabBtnImage, tabBtnLink].forEach(btn => {
      btn.classList.remove('active');
      btn.setAttribute('aria-selected', 'false');
    });
    [tabPanelText, tabPanelImage, tabPanelLink].forEach(panel => {
      panel.style.display = 'none';
    });

    if (tab === 'text') {
      tabBtnText.classList.add('active');
      tabBtnText.setAttribute('aria-selected', 'true');
      tabPanelText.style.display = 'block';
      textInput.focus();
    } else if (tab === 'image') {
      tabBtnImage.classList.add('active');
      tabBtnImage.setAttribute('aria-selected', 'true');
      tabPanelImage.style.display = 'block';
    } else if (tab === 'link') {
      tabBtnLink.classList.add('active');
      tabBtnLink.setAttribute('aria-selected', 'true');
      tabPanelLink.style.display = 'block';
      urlInput.focus();
    }
  }

  tabBtnText.addEventListener('click', () => setActiveTab('text'));
  tabBtnImage.addEventListener('click', () => setActiveTab('image'));
  tabBtnLink.addEventListener('click', () => setActiveTab('link'));
  window.addEventListener('beforeunload', stopCamera);

  // --- 2. Text Tab Handlers ---
  function updateWordCount() {
    const count = countWords(textInput.value);
    wordCounter.textContent = `${count} word${count === 1 ? '' : 's'}`;
    if (count > 0 && count < 50) {
      wordValidationMsg.style.display = 'inline';
    } else {
      wordValidationMsg.style.display = 'none';
    }
  }

  textInput.addEventListener('input', updateWordCount);

  clearTextBtn.addEventListener('click', () => {
    textInput.value = '';
    updateWordCount();
    textInput.focus();
  });

  // --- 3. Image OCR & Camera Handlers (P10) ---
  async function startCamera() {
    cameraErrorAlert.style.display = 'none';
    importDeviceBtn.classList.remove('btn-highlight');

    // Check getUserMedia support
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      showCameraError();
      return;
    }

    try {
      stopCamera(); // Clean any previous stream
      const constraints = {
        video: {
          facingMode: currentFacingMode,
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        },
        audio: false
      };

      currentCameraStream = await navigator.mediaDevices.getUserMedia(constraints);
      cameraVideo.srcObject = currentCameraStream;
      await cameraVideo.play();

      imageDropzone.style.display = 'none';
      cameraPreviewContainer.style.display = 'block';
    } catch (err) {
      console.warn('Camera access denied or failed:', err);
      showCameraError();
    }
  }

  function showCameraError() {
    cameraErrorAlert.style.display = 'block';
    importDeviceBtn.classList.add('btn-highlight');
    if (imageDropzone) imageDropzone.style.display = 'flex';
    if (cameraPreviewContainer) cameraPreviewContainer.style.display = 'none';
  }

  openCameraBtn.addEventListener('click', () => {
    startCamera();
  });

  cameraSwitchBtn.addEventListener('click', () => {
    currentFacingMode = currentFacingMode === 'environment' ? 'user' : 'environment';
    startCamera();
  });

  cameraCancelBtn.addEventListener('click', () => {
    stopCamera();
  });

  cameraCaptureBtn.addEventListener('click', () => {
    if (!cameraVideo.videoWidth || !cameraVideo.videoHeight) return;

    // Draw video frame to canvas
    cameraCanvas.width = cameraVideo.videoWidth;
    cameraCanvas.height = cameraVideo.videoHeight;
    const ctx = cameraCanvas.getContext('2d');
    ctx.drawImage(cameraVideo, 0, 0, cameraCanvas.width, cameraCanvas.height);

    // Stop camera immediately upon capture
    stopCamera();

    // Export frame as JPEG blob and trigger OCR
    cameraCanvas.toBlob(blob => {
      if (blob) {
        processImageFileOrBlob(blob, 'camera_capture.jpg');
      }
    }, 'image/jpeg', 0.95);
  });

  importDeviceBtn.addEventListener('click', () => {
    importDeviceBtn.classList.remove('btn-highlight');
    imageFileInput.click();
  });

  imageFileInput.addEventListener('change', e => {
    const file = e.target.files && e.target.files[0];
    if (file) {
      processImageFileOrBlob(file, file.name);
    }
  });

  // Drag-and-drop zone handlers
  ['dragenter', 'dragover'].forEach(eventName => {
    imageDropzone.addEventListener(eventName, e => {
      e.preventDefault();
      e.stopPropagation();
      imageDropzone.classList.add('dragover');
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    imageDropzone.addEventListener(eventName, e => {
      e.preventDefault();
      e.stopPropagation();
      imageDropzone.classList.remove('dragover');
    }, false);
  });

  imageDropzone.addEventListener('drop', e => {
    const dt = e.dataTransfer;
    const file = dt && dt.files && dt.files[0];
    if (file) {
      processImageFileOrBlob(file, file.name);
    }
  });

  imageDropzone.addEventListener('click', () => {
    imageFileInput.click();
  });

  // Send Image to POST /api/ocr with scanning laser animation
  async function processImageFileOrBlob(fileOrBlob, filename = 'image.jpg') {
    // Reset views
    cameraErrorAlert.style.display = 'none';
    ocrErrorAlert.style.display = 'none';
    ocrResultContainer.style.display = 'none';
    imageDropzone.style.display = 'none';
    stopCamera();

    // Client-side file size check (5 MB)
    if (fileOrBlob.size > 5 * 1024 * 1024) {
      ocrErrorAlert.style.display = 'block';
      ocrErrorText.textContent = 'Image file exceeds the 5 MB limit. Please choose a smaller photo.';
      imageDropzone.style.display = 'flex';
      return;
    }

    // Set preview image & start scanning laser
    const previewUrl = URL.createObjectURL(fileOrBlob);
    ocrPreviewImg.src = previewUrl;
    imageScanningContainer.style.display = 'block';
    ocrLaser.style.display = 'block';
    ocrStatusMsg.textContent = 'Reading text from image...';

    // Prepare multipart form data
    const formData = new FormData();
    formData.append('image', fileOrBlob, filename);

    try {
      const response = await darFetch('/api/ocr', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      // Stop laser animation
      ocrLaser.style.display = 'none';
      ocrStatusMsg.textContent = 'OCR Processing Complete';

      if (!response.ok) {
        ocrErrorAlert.style.display = 'block';
        ocrErrorText.textContent = data.message || data.error || "We couldn't read any text. Try a clearer photo or paste the text instead.";
      } else {
        ocrExtractedTextarea.value = data.text;
        ocrResultContainer.style.display = 'block';
        const count = countWords(data.text);
        ocrWordCounter.textContent = `${count} word${count === 1 ? '' : 's'}`;
        showToast('Text extracted from image. Review and click Analyze.', 'success');
      }
    } catch (err) {
      ocrLaser.style.display = 'none';
      ocrErrorAlert.style.display = 'block';
      ocrErrorText.textContent = "We couldn't read any text. Try a clearer photo or paste the text instead.";
    }
  }

  ocrExtractedTextarea.addEventListener('input', () => {
    const count = countWords(ocrExtractedTextarea.value);
    ocrWordCounter.textContent = `${count} word${count === 1 ? '' : 's'}`;
  });

  ocrRetakeBtn.addEventListener('click', () => {
    ocrResultContainer.style.display = 'none';
    imageScanningContainer.style.display = 'none';
    ocrErrorAlert.style.display = 'none';
    imageDropzone.style.display = 'flex';
    imageFileInput.value = '';
  });

  // --- 4. Link Fetcher Tab Handlers ---
  fetchedTextArea.addEventListener('input', () => {
    const count = countWords(fetchedTextArea.value);
    fetchedWordCounter.textContent = `${count} word${count === 1 ? '' : 's'}`;
  });

  fetchUrlBtn.addEventListener('click', async () => {
    const url = urlInput.value.trim();
    if (!url) {
      fetchErrorBox.textContent = 'Please enter a URL starting with http:// or https://.';
      fetchErrorBox.style.display = 'block';
      return;
    }

    fetchErrorBox.style.display = 'none';
    fetchBtnSpinner.style.display = 'inline-block';
    fetchBtnText.textContent = 'Fetching...';
    fetchUrlBtn.disabled = true;

    try {
      const response = await darFetch('/api/fetch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });

      const data = await response.json();
      if (!response.ok) {
        fetchErrorBox.textContent = data.error || "We couldn't read that page (it may need a login). Paste the text instead.";
        fetchErrorBox.style.display = 'block';
      } else {
        fetchedTextArea.value = data.text;
        fetchedContainer.style.display = 'block';
        const count = countWords(data.text);
        fetchedWordCounter.textContent = `${count} words`;
        showToast('Job text fetched successfully. Review and click Analyze.', 'success');
      }
    } catch (err) {
      fetchErrorBox.textContent = "We couldn't connect to that page. Please paste the text instead.";
      fetchErrorBox.style.display = 'block';
    } finally {
      fetchBtnSpinner.style.display = 'none';
      fetchBtnText.textContent = 'Fetch ad';
      fetchUrlBtn.disabled = false;
    }
  });

  // --- 5. Model Switcher (Segmented Control) ---
  modelBtnLr.addEventListener('click', () => {
    selectedModel = 'lr';
    modelBtnLr.classList.add('active');
    modelBtnRf.classList.remove('active');
  });

  modelBtnRf.addEventListener('click', () => {
    selectedModel = 'rf';
    modelBtnRf.classList.add('active');
    modelBtnLr.classList.remove('active');
  });

  // --- 6. Analyze Action & Execution ---
  function getAnalysisText() {
    if (activeTab === 'image') {
      return (ocrExtractedTextarea.value || '').trim();
    }
    if (activeTab === 'link') {
      return (fetchedTextArea.value || '').trim();
    }
    return (textInput.value || '').trim();
  }

  analyzeBtn.addEventListener('click', async () => {
    const text = getAnalysisText();
    analyzeErrorAlert.style.display = 'none';

    // Client-side validations
    if (!text) {
      analyzeErrorMsg.textContent = 'Please paste the job ad text to analyze.';
      analyzeErrorAlert.style.display = 'block';
      if (activeTab === 'image') {
        importDeviceBtn.focus();
      } else if (activeTab === 'link' && !fetchedTextArea.value) {
        urlInput.focus();
      } else {
        textInput.focus();
      }
      return;
    }

    const wordCount = countWords(text);
    if (wordCount < 50) {
      analyzeErrorMsg.textContent = 'Please paste the full ad (at least 50 words).';
      analyzeErrorAlert.style.display = 'block';
      return;
    }

    // Set button loading state
    analyzeBtn.disabled = true;
    analyzeSpinner.style.display = 'inline-block';
    analyzeIcon.style.display = 'none';
    analyzeText.textContent = 'Analyzing...';

    try {
      const response = await darFetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text,
          model: selectedModel,
          source: activeTab
        })
      });

      const data = await response.json();
      if (!response.ok) {
        analyzeErrorMsg.textContent = data.error || 'Analysis failed. Please try again.';
        analyzeErrorAlert.style.display = 'block';
        tempResultBlock.style.display = 'none';
      } else {
        renderResult(data);
      }
    } catch (err) {
      analyzeErrorMsg.textContent = 'Network error while analyzing. Please check your connection.';
      analyzeErrorAlert.style.display = 'block';
    } finally {
      analyzeBtn.disabled = false;
      analyzeSpinner.style.display = 'none';
      analyzeIcon.style.display = 'inline-block';
      analyzeText.textContent = 'Analyze';
    }
  });

  // --- 7. Render Temporary Result Block ---
  function renderResult(data) {
    const { verdict, probability, threshold, model_name, flags, top_fake_words, top_real_words, highlighted_html, ad_id } = data;

    // Verdict Badge & Colors
    verdictBadge.textContent = verdict;
    verdictBadge.className = 'badge';

    if (verdict === 'Likely Fake') {
      verdictBadge.classList.add('badge-fake');
      verdictIconContainer.innerHTML = '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2.2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>';
      verdictSubtitle.textContent = 'High probability of fraud. Do not send money or personal details.';
    } else if (verdict === 'Likely Real') {
      verdictBadge.classList.add('badge-real');
      verdictIconContainer.innerHTML = '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#16A34A" stroke-width="2.2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>';
      verdictSubtitle.textContent = 'Looks legitimate. Still verify the company independently.';
    } else {
      verdictBadge.classList.add('badge-warn');
      verdictIconContainer.innerHTML = '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="2.2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>';
      verdictSubtitle.textContent = 'Uncertain score. Please verify the company on its official portal.';
    }

    resultProbability.textContent = `Chance Fake: ${(probability * 100).toFixed(1)}%`;
    resultThreshold.textContent = `Decision Threshold: ${(threshold * 100).toFixed(1)}%`;
    resultModelName.textContent = model_name;

    // Warning Flags
    if (flags && flags.length > 0) {
      resultFlagsList.innerHTML = '';
      flags.forEach(f => {
        const li = document.createElement('li');
        li.style.fontSize = '0.9375rem';
        li.style.color = 'var(--text)';
        li.innerHTML = `<span class="badge badge-warn" style="font-size: 0.6875rem; margin-right: 0.5rem;">${f.code}</span>${f.message}`;
        resultFlagsList.appendChild(li);
      });
      resultFlagsContainer.style.display = 'block';
    } else {
      resultFlagsContainer.style.display = 'none';
    }

    // Top Fake Words Chips
    resultFakeWords.innerHTML = '';
    if (top_fake_words && top_fake_words.length > 0) {
      top_fake_words.forEach(w => {
        const chip = document.createElement('span');
        chip.className = 'chip';
        chip.style.backgroundColor = 'var(--fake-soft)';
        chip.style.color = 'var(--fake)';
        chip.style.borderColor = 'rgba(220, 38, 38, 0.2)';
        chip.textContent = `${w.word} (+${w.weight})`;
        resultFakeWords.appendChild(chip);
      });
    } else {
      resultFakeWords.innerHTML = '<span class="caption">None identified</span>';
    }

    // Top Real Words Chips
    resultRealWords.innerHTML = '';
    if (top_real_words && top_real_words.length > 0) {
      top_real_words.forEach(w => {
        const chip = document.createElement('span');
        chip.className = 'chip';
        chip.style.backgroundColor = 'var(--real-soft)';
        chip.style.color = 'var(--real)';
        chip.style.borderColor = 'rgba(22, 163, 74, 0.2)';
        chip.textContent = `${w.word} (-${w.weight})`;
        resultRealWords.appendChild(chip);
      });
    } else {
      resultRealWords.innerHTML = '<span class="caption">None identified</span>';
    }

    // Highlighted HTML text
    resultHighlightedText.innerHTML = highlighted_html || '';

    // Result link
    viewFullResultLink.href = `/result/${ad_id}`;

    // Reveal result block
    tempResultBlock.style.display = 'block';
    tempResultBlock.scrollIntoView({ behavior: 'smooth', block: 'start' });

    showToast(`Analysis complete: Verdict is ${verdict}.`, 'info');
  }
});
