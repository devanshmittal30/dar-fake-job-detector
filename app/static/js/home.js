/**
 * home.js — Interactive controller for the DAR Home page
 * Following docs/02_UI_UX_SPEC.md (section 6 and 10) and roadmap prompt P14:
 * - Proof boxes populated dynamically from GET /api/home
 * - Smooth count-up animations for numbers (respecting prefers-reduced-motion)
 * - Ratings summary, star distribution bars, and approved reviews
 * - Honest empty states (no placeholder reviews or made-up statistics)
 */

document.addEventListener('DOMContentLoaded', () => {
  // Elements: Proof Boxes
  const proofAnalyses = document.getElementById('proof-analyses');
  const proofTrainingRows = document.getElementById('proof-training-rows');
  const proofAccuracy = document.getElementById('proof-accuracy');
  const proofRecall = document.getElementById('proof-recall');
  const proofPrecision = document.getElementById('proof-precision');

  // Elements: Ratings & Reviews
  const ratingsLoading = document.getElementById('ratings-loading');
  const ratingsContent = document.getElementById('ratings-content');
  const ratingsEmptyState = document.getElementById('ratings-empty-state');
  const summaryAvg = document.getElementById('summary-avg');
  const summaryStars = document.getElementById('summary-stars');
  const summaryCount = document.getElementById('summary-count');
  const reviewsGrid = document.getElementById('reviews-grid');
  const noReviewsNote = document.getElementById('no-reviews-note');

  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function renderStars(rating) {
    const fullStars = Math.round(rating);
    let str = '';
    for (let i = 1; i <= 5; i++) {
      str += i <= fullStars ? '★' : '☆';
    }
    return str;
  }

  function animateNumber(element, target, duration = 1200, suffix = '') {
    if (!element) return;
    if (prefersReducedMotion || typeof target !== 'number') {
      element.textContent = (typeof target === 'number' ? target.toLocaleString() : target) + suffix;
      return;
    }

    const startTime = performance.now();
    const isFloat = String(target).includes('.');

    function step(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // easeOutExpo
      const ease = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
      const val = target * ease;

      if (isFloat) {
        element.textContent = val.toFixed(1) + suffix;
      } else {
        element.textContent = Math.round(val).toLocaleString() + suffix;
      }

      if (progress < 1) {
        requestAnimationFrame(step);
      } else {
        element.textContent = (isFloat ? target.toFixed(1) : target.toLocaleString()) + suffix;
      }
    }

    requestAnimationFrame(step);
  }

  async function loadHomeData() {
    try {
      const resp = await fetch('/api/home');
      if (!resp.ok) {
        throw new Error('Failed to load home data');
      }

      const data = await resp.json();

      // 1. Fill Proof Boxes
      if (proofAnalyses) {
        const total = typeof data.analyses_total === 'number' ? data.analyses_total : 0;
        animateNumber(proofAnalyses, total);
      }

      if (proofTrainingRows) {
        if (typeof data.training_rows === 'number') {
          proofTrainingRows.textContent = data.training_rows.toLocaleString();
        } else {
          proofTrainingRows.textContent = data.training_rows || 'n/a';
        }
      }

      if (proofAccuracy) {
        if (typeof data.accuracy === 'number') {
          animateNumber(proofAccuracy, data.accuracy, 1200, '%');
        } else {
          proofAccuracy.textContent = data.accuracy || 'n/a';
        }
      }

      if (proofRecall) {
        proofRecall.textContent = typeof data.recall === 'number' ? `${data.recall}%` : (data.recall || 'n/a');
      }

      if (proofPrecision) {
        proofPrecision.textContent = typeof data.precision === 'number' ? `${data.precision}%` : (data.precision || 'n/a');
      }

      // 2. Fill Ratings Section
      if (ratingsLoading) ratingsLoading.style.display = 'none';

      const ratingCount = data.rating_count || 0;
      const avg = data.avg_rating;

      if (ratingCount === 0 || avg === null || avg === undefined) {
        if (ratingsEmptyState) ratingsEmptyState.style.display = 'block';
        if (ratingsContent) ratingsContent.style.display = 'none';
      } else {
        if (ratingsContent) ratingsContent.style.display = 'grid';
        if (ratingsEmptyState) ratingsEmptyState.style.display = 'none';

        if (summaryAvg) summaryAvg.textContent = avg.toFixed(1);
        if (summaryStars) summaryStars.textContent = renderStars(avg);
        if (summaryCount) {
          summaryCount.textContent = `Based on ${ratingCount.toLocaleString()} rating${ratingCount === 1 ? '' : 's'}`;
        }

        // Star distribution bars
        const dist = data.distribution || {};
        for (let s = 1; s <= 5; s++) {
          const count = dist[String(s)] || 0;
          const barEl = document.getElementById(`dist-bar-${s}`);
          const countEl = document.getElementById(`dist-count-${s}`);
          const pct = ratingCount > 0 ? (count / ratingCount) * 100 : 0;

          if (barEl) barEl.style.width = `${pct}%`;
          if (countEl) countEl.textContent = count.toLocaleString();
        }

        // Reviews Grid (up to 6 approved 4-5 star reviews)
        const reviews = data.reviews || [];
        if (reviewsGrid) {
          reviewsGrid.innerHTML = '';
          if (reviews.length === 0) {
            if (noReviewsNote) noReviewsNote.style.display = 'block';
          } else {
            if (noReviewsNote) noReviewsNote.style.display = 'none';
            reviews.forEach(rev => {
              const card = document.createElement('div');
              card.className = 'review-card';
              card.innerHTML = `
                <div style="color: #F59E0B; font-size: 1.125rem; margin-bottom: 0.5rem;" aria-label="${rev.stars} stars">
                  ${'★'.repeat(rev.stars)}${'☆'.repeat(5 - rev.stars)}
                </div>
                <p style="font-size: 0.9375rem; line-height: 1.5; color: var(--text); margin-bottom: 1rem; flex-grow: 1;">
                  "${escapeHtml(rev.comment)}"
                </p>
                <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border); padding-top: 0.75rem; margin-top: auto;">
                  <strong style="font-size: 0.875rem;">${escapeHtml(rev.first_name)}</strong>
                  <span class="caption text-muted">${escapeHtml(rev.date)}</span>
                </div>
              `;
              reviewsGrid.appendChild(card);
            });
          }
        }
      }
    } catch (err) {
      console.warn('Could not load home page metrics:', err);
      if (ratingsLoading) ratingsLoading.style.display = 'none';
      if (ratingsEmptyState) ratingsEmptyState.style.display = 'block';
    }
  }

  loadHomeData();
});
