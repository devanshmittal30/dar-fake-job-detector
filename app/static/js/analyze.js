/**
 * analyze.js — Client-side interaction logic for the Analyze Job page
 * Following docs/02_UI_UX_SPEC.md (section 7) and prompt P9
 */

document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const tabBtnText = document.getElementById('tab-btn-text');
  const tabBtnImage = document.getElementById('tab-btn-image');
  const tabBtnLink = document.getElementById('tab-btn-link');
  const tabPanelText = document.getElementById('tab-panel-text');
  const tabPanelImage = document.getElementById('tab-panel-image');
  const tabPanelLink = document.getElementById('tab-panel-link');
  const switchToTextTab = document.getElementById('switch-to-text-tab');

  const textInput = document.getElementById('job-text-input');
  const clearTextBtn = document.getElementById('clear-text-btn');
  const wordCounter = document.getElementById('word-counter');
  const wordValidationMsg = document.getElementById('word-validation-msg');

  const urlInput = document.getElementById('job-url-input');
  const fetchUrlBtn = document.getElementById('fetch-url-btn');
  const fetchBtnSpinner = document.getElementById('fetch-btn-spinner');
  const fetchBtnText = document.getElementById('fetch-btn-text');
  const fetchErrorBox = document.getElementById('fetch-error-box');
  const fetchedContainer = document.getElementById('fetched-text-container');
  const fetchedTextArea = document.getElementById('fetched-text-area');
  const fetchedWordCounter = document.getElementById('fetched-word-counter');

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

  let activeTab = 'text';
  let selectedModel = 'lr';

  // --- 1. Tab Navigation ---
  function setActiveTab(tab) {
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
  if (switchToTextTab) {
    switchToTextTab.addEventListener('click', () => setActiveTab('text'));
  }

  // --- 2. Live Word Counter ---
  function countWords(str) {
    if (!str || !str.trim()) return 0;
    return str.trim().split(/\s+/).length;
  }

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

  fetchedTextArea.addEventListener('input', () => {
    const count = countWords(fetchedTextArea.value);
    fetchedWordCounter.textContent = `${count} word${count === 1 ? '' : 's'}`;
  });

  // --- 3. Model Switcher (Segmented Control) ---
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

  // --- 4. Link Fetcher ---
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

  // --- 5. Analyze Action ---
  function getAnalysisText() {
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
      if (activeTab === 'link' && !fetchedTextArea.value) {
        urlInput.focus();
      } else {
        textInput.focus();
      }
      return;
    }

    const wordCount = countWords(text);
    if (wordCount < 50) {
      analyzeErrorMsg.textContent = `Please paste the full ad (at least 50 words). Current: ${wordCount} words.`;
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

  // --- 6. Render Temporary Result Block ---
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
