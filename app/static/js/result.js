/**
 * result.js — Interactive behaviors for the DAR Result page
 * Following docs/02_UI_UX_SPEC.md (section 8) and roadmap prompt P11:
 * - Confidence gauge sweep animation and number count-up (respects prefers-reduced-motion)
 * - Copy link to clipboard with toast notification
 * - Community verification modal trigger (voting wired in P13)
 * - Interactive star rating and comment character counter
 */

document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const gaugeFillArc = document.getElementById('gauge-fill-arc');
  const gaugeNumber = document.getElementById('gauge-number');
  const copyLinkBtn = document.getElementById('copy-result-link-btn');

  // Voting Elements
  const voteGenuineBtn = document.getElementById('vote-genuine-btn');
  const voteFakeBtn = document.getElementById('vote-fake-btn');
  const loginModal = document.getElementById('login-modal');
  const closeModalBtn = document.getElementById('close-modal-btn');

  // Rating Elements
  const starRatingContainer = document.getElementById('star-rating');
  const ratingComment = document.getElementById('rating-comment');
  const commentCounter = document.getElementById('comment-counter');
  const submitRatingBtn = document.getElementById('submit-rating-btn');

  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // --- 1. Semicircle Gauge Sweep & Number Count-Up ---
  if (gaugeFillArc && gaugeNumber) {
    const targetOffset = parseFloat(gaugeFillArc.dataset.targetOffset || '0');
    const targetNumber = parseFloat(gaugeNumber.dataset.target || '0');

    if (prefersReducedMotion) {
      gaugeFillArc.style.strokeDashoffset = targetOffset;
      gaugeNumber.textContent = `${targetNumber.toFixed(1)}%`;
    } else {
      // Trigger SVG gauge stroke animation
      requestAnimationFrame(() => {
        setTimeout(() => {
          gaugeFillArc.style.strokeDashoffset = targetOffset;
        }, 150);
      });

      // Animate percentage count-up
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
        // Fallback for non-secure contexts
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

  // --- 3. Community Verification Modal (TEMPORARY: full voting wired in P13) ---
  function openLoginModal() {
    if (loginModal) {
      loginModal.style.display = 'flex';
      document.body.style.overflow = 'hidden';
    }
  }

  function closeLoginModal() {
    if (loginModal) {
      loginModal.style.display = 'none';
      document.body.style.overflow = '';
    }
  }

  if (voteGenuineBtn) voteGenuineBtn.addEventListener('click', openLoginModal);
  if (voteFakeBtn) voteFakeBtn.addEventListener('click', openLoginModal);
  if (closeModalBtn) closeModalBtn.addEventListener('click', closeLoginModal);

  if (loginModal) {
    loginModal.addEventListener('click', e => {
      if (e.target === loginModal) {
        closeLoginModal();
      }
    });
  }

  // --- 4. Star Rating & Comment Counter ---
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
    submitRatingBtn.addEventListener('click', () => {
      if (selectedRating === 0) {
        if (typeof showToast === 'function') {
          showToast('Please select a star rating (1 to 5).', 'warn');
        }
        return;
      }

      if (typeof showToast === 'function') {
        showToast('Thank you! Ratings will be wired with your user account in Stage 5.', 'success');
      }
      submitRatingBtn.disabled = true;
      submitRatingBtn.textContent = 'Rating Recorded';
    });
  }
});
