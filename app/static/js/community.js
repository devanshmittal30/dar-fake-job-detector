/**
 * community.js — Interactive controller for the DAR Community Reports page
 * Following docs/02_UI_UX_SPEC.md (section 9.1) and roadmap prompt P13:
 * - Real-time keyword search
 * - Filter chips: All, Marked fake, Marked genuine, Disputed
 * - Sort: Newest, Most votes
 * - Dynamic rendering of AdCards with verdict badge, VoteBar, counts, and time ago
 * - Pagination controls and honest empty states
 */

document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const searchInput = document.getElementById('community-search');
  const filterChips = document.querySelectorAll('.filter-chip');
  const sortSelect = document.getElementById('community-sort');
  const gridContainer = document.getElementById('community-grid');
  const loadingIndicator = document.getElementById('community-loading');
  const emptyBoardEl = document.getElementById('community-empty-board');
  const emptyFilterEl = document.getElementById('community-empty-filter');
  const paginationWrapper = document.getElementById('community-pagination');
  const prevPageBtn = document.getElementById('prev-page-btn');
  const nextPageBtn = document.getElementById('next-page-btn');
  const pageIndicator = document.getElementById('page-indicator');
  const resetFiltersBtn = document.getElementById('reset-filters-btn');

  // State
  let currentFilter = 'all';
  let currentQuery = '';
  let currentSort = 'newest';
  let currentPage = 1;
  let totalPages = 1;
  let searchDebounceTimer = null;

  function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function getVerdictBadge(label) {
    if (label === 'Likely Fake' || label === 'Fake') {
      return '<span class="badge badge-fake">Likely FAKE</span>';
    } else if (label === 'Likely Real' || label === 'Real') {
      return '<span class="badge badge-real">Likely REAL</span>';
    }
    return '<span class="badge badge-warn">UNCERTAIN</span>';
  }

  async function fetchCommunityReports() {
    // Show loading
    if (loadingIndicator) loadingIndicator.style.display = 'block';
    if (gridContainer) gridContainer.style.display = 'none';
    if (emptyBoardEl) emptyBoardEl.style.display = 'none';
    if (emptyFilterEl) emptyFilterEl.style.display = 'none';
    if (paginationWrapper) paginationWrapper.style.display = 'none';

    try {
      const params = new URLSearchParams({
        filter: currentFilter,
        q: currentQuery,
        sort: currentSort,
        page: currentPage
      });

      const resp = await fetch(`/api/community?${params.toString()}`);
      if (!resp.ok) {
        throw new Error('Failed to fetch community reports');
      }

      const data = await resp.json();
      renderReports(data);
    } catch (err) {
      console.error('Community fetch error:', err);
      if (loadingIndicator) loadingIndicator.style.display = 'none';
      if (typeof showToast === 'function') {
        showToast('Could not load community reports.', 'error');
      }
    }
  }

  function renderReports(data) {
    if (loadingIndicator) loadingIndicator.style.display = 'none';

    const items = data.items || [];
    const total = data.total || 0;
    currentPage = data.page || 1;
    totalPages = data.pages || 1;

    // 1. Check for empty states
    if (total === 0) {
      if (currentFilter === 'all' && !currentQuery) {
        if (emptyBoardEl) emptyBoardEl.style.display = 'block';
      } else {
        if (emptyFilterEl) emptyFilterEl.style.display = 'block';
      }
      return;
    }

    // 2. Render Cards Grid
    gridContainer.innerHTML = '';
    items.forEach(item => {
      const card = document.createElement('a');
      card.href = `/result/${encodeURIComponent(item.ad_id)}`;
      card.className = 'ad-card card-hover';
      card.setAttribute('role', 'article');
      card.setAttribute('aria-label', `Job ad evaluated as ${item.ai_label}`);

      const disputedBadge = item.is_disputed
        ? '<span class="badge badge-disputed" title="Community votes are closely split">Disputed</span>'
        : '';

      const totalVotes = item.total_votes || 0;
      let voteBarHtml = '';
      if (totalVotes === 0) {
        voteBarHtml = `
          <div class="vote-bar-wrapper" style="height: 6px; margin: 0.5rem 0;">
            <div style="width: 100%; background-color: var(--border);"></div>
          </div>
          <div class="ad-card-meta">No votes yet</div>
        `;
      } else {
        voteBarHtml = `
          <div class="vote-bar-wrapper" style="height: 6px; margin: 0.5rem 0;">
            <div class="vote-bar-fake" style="width: ${item.fake_percent}%;"></div>
            <div class="vote-bar-genuine" style="width: ${item.genuine_percent}%;"></div>
          </div>
          <div class="ad-card-meta" style="display: flex; justify-content: space-between;">
            <span><strong>${item.fake_votes}</strong> marked fake</span>
            <span><strong>${item.genuine_votes}</strong> marked genuine</span>
          </div>
        `;
      }

      card.innerHTML = `
        <div class="ad-card-top">
          <div style="display: flex; gap: 0.35rem; align-items: center; flex-wrap: wrap;">
            ${getVerdictBadge(item.ai_label)}
            ${disputedBadge}
          </div>
          <span class="caption text-muted">${escapeHtml(item.time_ago)}</span>
        </div>
        <p class="ad-card-snippet">${escapeHtml(item.snippet)}...</p>
        <div style="margin-top: auto;">
          ${voteBarHtml}
        </div>
      `;

      gridContainer.appendChild(card);
    });

    gridContainer.style.display = 'grid';

    // 3. Update Pagination
    if (totalPages > 1) {
      if (pageIndicator) {
        pageIndicator.textContent = `Page ${currentPage} of ${totalPages}`;
      }
      if (prevPageBtn) {
        prevPageBtn.disabled = currentPage <= 1;
      }
      if (nextPageBtn) {
        nextPageBtn.disabled = currentPage >= totalPages;
      }
      if (paginationWrapper) {
        paginationWrapper.style.display = 'flex';
      }
    } else {
      if (paginationWrapper) {
        paginationWrapper.style.display = 'none';
      }
    }
  }

  // Event Listeners: Filter Chips
  filterChips.forEach(chip => {
    chip.addEventListener('click', () => {
      filterChips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      currentFilter = chip.dataset.filter || 'all';
      currentPage = 1;
      fetchCommunityReports();
    });
  });

  // Event Listener: Search Input (Debounced 300ms)
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      clearTimeout(searchDebounceTimer);
      searchDebounceTimer = setTimeout(() => {
        currentQuery = searchInput.value.trim();
        currentPage = 1;
        fetchCommunityReports();
      }, 300);
    });
  }

  // Event Listener: Sort Select
  if (sortSelect) {
    sortSelect.addEventListener('change', () => {
      currentSort = sortSelect.value || 'newest';
      currentPage = 1;
      fetchCommunityReports();
    });
  }

  // Event Listener: Pagination Buttons
  if (prevPageBtn) {
    prevPageBtn.addEventListener('click', () => {
      if (currentPage > 1) {
        currentPage--;
        fetchCommunityReports();
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    });
  }

  if (nextPageBtn) {
    nextPageBtn.addEventListener('click', () => {
      if (currentPage < totalPages) {
        currentPage++;
        fetchCommunityReports();
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    });
  }

  // Event Listener: Reset Filters Button
  if (resetFiltersBtn) {
    resetFiltersBtn.addEventListener('click', () => {
      currentFilter = 'all';
      currentQuery = '';
      currentSort = 'newest';
      currentPage = 1;
      if (searchInput) searchInput.value = '';
      if (sortSelect) sortSelect.value = 'newest';
      filterChips.forEach(c => {
        if (c.dataset.filter === 'all') c.classList.add('active');
        else c.classList.remove('active');
      });
      fetchCommunityReports();
    });
  }

  // Initial Fetch
  fetchCommunityReports();
});
