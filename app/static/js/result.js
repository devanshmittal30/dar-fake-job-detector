/**
 * result.js — Interactive behaviors for the DAR Result page
 * Following docs/02_UI_UX_SPEC.md (sections 8.3 & 8.4) and roadmap prompt P13:
 * - Confidence gauge sweep animation and number count-up (respects prefers-reduced-motion)
 * - Copy link to clipboard with toast notification
 * - Live community verification:
 *     * Thumbs up ("genuine") and Thumbs down ("fake")
 *     * Vote uniqueness & changing a vote without reload
 *     * Stacked VoteBar with percentages & counts
 *     * Empty state: "No community votes yet. Be the first to verify this ad."
 *     * Selected state: "You marked this ad as fake. You can change your vote."
 *     * Amber disagreement note when AI verdict and vote majority (>= 3 votes) differ
 *     * Login modal for unauthenticated visitors
 * - Star rating (1-5) and comment box (max 200 chars) with approval note
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Core Elements
  const gaugeFillArc = document.getElementById('gauge-fill-arc');
  const gaugeNumber = document.getElementById('gauge-number');
  const copyLinkBtn = document.getElementById('copy-result-link-btn');

  // 2. Voting Elements
  const voteGenuineBtn = document.getElementById('vote-genuine-btn');
  const voteFakeBtn = document.getElementById('vote-fake-btn');
  const countFakeEl = document.getElementById('count-fake');
  const countGenuineEl = document.getElementById('count-genuine');
  const barFakeEl = document.getElementById('bar-fake');
  const barGenuineEl = document.getElementById('bar-genuine');
  const fakePctLabel = document.getElementById('fake-pct-label');
  const genuinePctLabel = document.getElementById('genuine-pct-label');
  const voteEmptyState = document.getElementById('vote-empty-state');
  const voteUserStatus = document.getElementById('vote-user-status');
  const disagreementBanner = document.getElementById('disagreement-banner');

  // 3. Modal Elements
  const loginModal = document.getElementById('login-modal');
  const closeModalBtn = document.getElementById('close-modal-btn');

  // 4. Rating Elements
  const starRatingContainer = document.getElementById('star-rating');
  const ratingComment = document.getElementById('rating-comment');
  const commentCounter = document.getElementById('comment-counter');
  const submitRatingBtn = document.getElementById('submit-rating-btn');
  const ratingNotice = document.getElementById('rating-notice');

  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Extract ad_id from URL: /result/<ad_id>
  const pathParts = window.location.pathname.split('/').filter(Boolean);
  const adId = pathParts[pathParts.length - 1];

  // --- 1. Semicircle Gauge Sweep & Number Count-Up ---
  if (gaugeFillArc && gaugeNumber) {
    const targetOffset = parseFloat(gaugeFillArc.dataset.targetOffset || '0');
    const targetNumber = parseFloat(gaugeNumber.dataset.target || '0');

    if (prefersReducedMotion) {
      gaugeFillArc.style.strokeDashoffset = targetOffset;
      gaugeNumber.textContent = `${targetNumber.toFixed(1)}%`;
    } else {
      requestAnimationFrame(() => {
        setTimeout(() => {
          gaugeFillArc.style.strokeDashoffset = targetOffset;
        }, 150);
      });

      const duration = 1200;
      const startTime = performance.now();

      function updateGaugeCount(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const ease = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
        const currentVal = targetNumber * ease;

        gaugeNumber.textContent = `${currentVal.toFixed(1)}%`;

        if (progress < 1) {
          requestAnimationFrame(updateGaugeCount);
        } else {
          gaugeNumber.textContent = `${targetNumber.toFixed(1)}%`;
        }
      }

      requestAnimationFrame(updateGaugeCount);
    }
  }

  // --- 2. Copy Link to Clipboard ---
  if (copyLinkBtn) {
    copyLinkBtn.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(window.location.href);
        if (typeof showToast === 'function') {
          showToast('Link copied to clipboard!', 'success');
        } else {
          alert('Link copied to clipboard!');
        }
      } catch (err) {
        const tempInput = document.createElement('input');
        tempInput.value = window.location.href;
        document.body.appendChild(tempInput);
        tempInput.select();
        document.execCommand('copy');
        document.body.removeChild(tempInput);
        if (typeof showToast === 'function') {
          showToast('Link copied to clipboard!', 'success');
        }
      }
    });
  }

  // --- 3. Login Modal Control with Accessibility Focus Trap ---
  let lastActiveElement = null;

  function openLoginModal() {
    if (loginModal) {
      lastActiveElement = document.activeElement;
      loginModal.style.display = 'flex';
      document.body.style.overflow = 'hidden';
      // Move focus to modal close button or first interactive element
      if (closeModalBtn) {
        closeModalBtn.focus();
      }
    }
  }

  function closeLoginModal() {
    if (loginModal) {
      loginModal.style.display = 'none';
      document.body.style.overflow = '';
      if (lastActiveElement && typeof lastActiveElement.focus === 'function') {
        lastActiveElement.focus();
      }
    }
  }

  if (closeModalBtn) closeModalBtn.addEventListener('click', closeLoginModal);
  if (loginModal) {
    loginModal.addEventListener('click', e => {
      if (e.target === loginModal) {
        closeLoginModal();
      }
    });

    // Keyboard support: Escape closes modal & Tab trap
    document.addEventListener('keydown', e => {
      if (loginModal.style.display === 'flex') {
        if (e.key === 'Escape') {
          e.preventDefault();
          closeLoginModal();
        } else if (e.key === 'Tab') {
          const focusable = loginModal.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
          if (focusable.length > 0) {
            const first = focusable[0];
            const last = focusable[focusable.length - 1];
            if (e.shiftKey && document.activeElement === first) {
              e.preventDefault();
              last.focus();
            } else if (!e.shiftKey && document.activeElement === last) {
              e.preventDefault();
              first.focus();
            }
          }
        }
      }
    });
  }

  // --- 4. Render Vote UI State ---
  function updateVoteUI(data) {
    const fakeCount = data.fake_votes || 0;
    const genuineCount = data.genuine_votes || 0;
    const totalVotes = fakeCount + genuineCount;

    // Update numbers
    if (countFakeEl) countFakeEl.textContent = fakeCount.toLocaleString();
    if (countGenuineEl) countGenuineEl.textContent = genuineCount.toLocaleString();

    if (totalVotes === 0) {
      if (barFakeEl) barFakeEl.style.width = '0%';
      if (barGenuineEl) barGenuineEl.style.width = '0%';
      if (fakePctLabel) fakePctLabel.textContent = '';
      if (genuinePctLabel) genuinePctLabel.textContent = '';
      if (voteEmptyState) voteEmptyState.style.display = 'block';
    } else {
      const fakePct = data.fake_percent !== undefined ? data.fake_percent : Math.round((fakeCount / totalVotes) * 100);
      const genuinePct = data.genuine_percent !== undefined ? data.genuine_percent : Math.round((genuineCount / totalVotes) * 100);

      if (barFakeEl) {
        barFakeEl.style.width = `${fakePct}%`;
        barFakeEl.title = `Marked fake: ${fakePct}% (${fakeCount})`;
      }
      if (barGenuineEl) {
        barGenuineEl.style.width = `${genuinePct}%`;
        barGenuineEl.title = `Marked genuine: ${genuinePct}% (${genuineCount})`;
      }

      if (fakePctLabel) fakePctLabel.textContent = `Fake: ${fakePct}% (${fakeCount})`;
      if (genuinePctLabel) genuinePctLabel.textContent = `Genuine: ${genuinePct}% (${genuineCount})`;
      if (voteEmptyState) voteEmptyState.style.display = 'none';
    }

    // Selected state on buttons
    if (voteFakeBtn && voteGenuineBtn) {
      voteFakeBtn.classList.remove('selected');
      voteGenuineBtn.classList.remove('selected');

      if (data.my_vote === 'fake') {
        voteFakeBtn.classList.add('selected');
        if (voteUserStatus) {
          voteUserStatus.textContent = 'You marked this ad as fake. You can change your vote.';
          voteUserStatus.style.display = 'block';
        }
      } else if (data.my_vote === 'genuine') {
        voteGenuineBtn.classList.add('selected');
        if (voteUserStatus) {
          voteUserStatus.textContent = 'You marked this ad as genuine. You can change your vote.';
          voteUserStatus.style.display = 'block';
        }
      } else {
        if (voteUserStatus) voteUserStatus.style.display = 'none';
      }
    }

    // Disagreement note
    if (disagreementBanner) {
      if (data.disagreement) {
        disagreementBanner.style.display = 'flex';
      } else {
        disagreementBanner.style.display = 'none';
      }
    }
  }

  // --- 5. Load Initial Vote Data ---
  async function loadVoteDetails() {
    if (!adId) return;
    try {
      const resp = await fetch(`/api/ads/${encodeURIComponent(adId)}`);
      if (resp.ok) {
        const data = await resp.json();
        updateVoteUI(data);
      }
    } catch (err) {
      console.warn('Could not load community vote counts:', err);
    }
  }

  loadVoteDetails();

  // --- 6. Cast or Change Vote ---
  async function castVote(voteType) {
    if (!adId) return;

    try {
      const resp = await darFetch(`/api/ads/${encodeURIComponent(adId)}/vote`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vote: voteType })
      });

      if (resp.status === 401) {
        // User not logged in
        openLoginModal();
        return;
      }

      const data = await resp.json();
      if (resp.ok) {
        updateVoteUI(data);
        if (typeof showToast === 'function') {
          showToast(`Vote recorded: marked as ${voteType}.`, 'success');
        }
      } else {
        if (typeof showToast === 'function') {
          showToast(data.error || 'Failed to submit vote.', 'error');
        }
      }
    } catch (err) {
      console.error('Vote submission failed:', err);
    }
  }

  if (voteGenuineBtn) {
    voteGenuineBtn.addEventListener('click', () => castVote('genuine'));
  }
  if (voteFakeBtn) {
    voteFakeBtn.addEventListener('click', () => castVote('fake'));
  }

  // --- 7. Star Rating & Comment Counter ---
  let selectedRating = 0;

  if (starRatingContainer) {
    const stars = starRatingContainer.querySelectorAll('.star-item');

    stars.forEach(star => {
      star.addEventListener('click', () => {
        selectedRating = parseInt(star.dataset.val, 10);
        updateStars();
      });

      star.addEventListener('mouseenter', () => {
        const hoverVal = parseInt(star.dataset.val, 10);
        highlightStars(hoverVal);
      });
    });

    starRatingContainer.addEventListener('mouseleave', () => {
      updateStars();
    });

    function highlightStars(val) {
      stars.forEach(s => {
        const sVal = parseInt(s.dataset.val, 10);
        if (sVal <= val) {
          s.classList.add('active');
        } else {
          s.classList.remove('active');
        }
      });
    }

    function updateStars() {
      highlightStars(selectedRating);
    }
  }

  if (ratingComment && commentCounter) {
    ratingComment.addEventListener('input', () => {
      const len = ratingComment.value.length;
      commentCounter.textContent = `${len} / 200`;
    });
  }

  if (submitRatingBtn) {
    submitRatingBtn.addEventListener('click', async () => {
      if (selectedRating === 0) {
        if (typeof showToast === 'function') {
          showToast('Please select a star rating (1 to 5).', 'warn');
        }
        return;
      }

      const commentText = ratingComment ? ratingComment.value.trim() : '';

      submitRatingBtn.disabled = true;
      submitRatingBtn.textContent = 'Submitting...';

      try {
        const resp = await darFetch(`/api/ads/${encodeURIComponent(adId)}/rating`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            stars: selectedRating,
            comment: commentText
          })
        });

        if (resp.status === 401) {
          openLoginModal();
          submitRatingBtn.disabled = false;
          submitRatingBtn.textContent = 'Submit rating';
          return;
        }

        const data = await resp.json();
        if (resp.ok) {
          if (ratingNotice) {
            ratingNotice.style.display = 'inline-block';
          }
          if (typeof showToast === 'function') {
            showToast('Thank you! Your rating has been submitted.', 'success');
          }
          submitRatingBtn.textContent = 'Rating Submitted';
          if (ratingComment) ratingComment.disabled = true;
        } else {
          submitRatingBtn.disabled = false;
          submitRatingBtn.textContent = 'Submit rating';
          if (typeof showToast === 'function') {
            showToast(data.error || 'Failed to submit rating.', 'error');
          }
        }
      } catch (err) {
        submitRatingBtn.disabled = false;
        submitRatingBtn.textContent = 'Submit rating';
        console.error('Rating failed:', err);
      }
    });
  }
});
