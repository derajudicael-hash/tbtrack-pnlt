/**
 * search.js — Autocomplete de la barre de recherche topbar
 * TBTrack v0.2
 */

'use strict';

(function () {
  const input = document.getElementById('searchInput');
  const dropdown = document.getElementById('searchDropdown');
  if (!input || !dropdown) return;

  let debounceTimer = null;
  let selectedIndex = -1;
  let suggestions = [];

  // ── Debounce de 300ms ─────────────────────────────────────────────────────

  input.addEventListener('input', function () {
    clearTimeout(debounceTimer);
    const q = this.value.trim();
    if (q.length < 2) {
      closeDropdown();
      return;
    }
    debounceTimer = setTimeout(function () {
      fetchSuggestions(q);
    }, 300);
  });

  // ── Requête AJAX ──────────────────────────────────────────────────────────

  function fetchSuggestions(q) {
    fetch('/search/?q=' + encodeURIComponent(q), {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        suggestions = data.resultats || [];
        renderDropdown(suggestions);
      })
      .catch(function () {
        closeDropdown();
      });
  }

  // ── Rendu du dropdown ─────────────────────────────────────────────────────

  function renderDropdown(items) {
    selectedIndex = -1;
    if (items.length === 0) {
      closeDropdown();
      return;
    }

    dropdown.innerHTML = '';
    items.forEach(function (item, i) {
      const div = document.createElement('div');
      div.className = 'search-item';
      div.dataset.index = i;
      div.innerHTML =
        '<span class="search-code">' + escHtml(item.code) + '</span>' +
        '<span class="search-nom">' + escHtml(item.nom) + '</span>' +
        '<span class="badge bg-' + escHtml(item.statut_badge) + ' ms-auto">' + escHtml(item.statut) + '</span>' +
        (item.resistance ? '<span class="search-res ms-1">' + escHtml(item.resistance) + '</span>' : '');
      div.addEventListener('mousedown', function (e) {
        e.preventDefault();
        window.location.href = item.url;
      });
      div.addEventListener('mouseover', function () {
        setActive(i);
      });
      dropdown.appendChild(div);
    });

    dropdown.classList.remove('d-none');
  }

  // ── Navigation clavier ────────────────────────────────────────────────────

  input.addEventListener('keydown', function (e) {
    const items = dropdown.querySelectorAll('.search-item');
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActive(Math.min(selectedIndex + 1, items.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActive(Math.max(selectedIndex - 1, 0));
    } else if (e.key === 'Enter') {
      if (selectedIndex >= 0 && suggestions[selectedIndex]) {
        e.preventDefault();
        window.location.href = suggestions[selectedIndex].url;
      }
    } else if (e.key === 'Escape') {
      closeDropdown();
    }
  });

  function setActive(index) {
    const items = dropdown.querySelectorAll('.search-item');
    items.forEach(function (el) { el.classList.remove('active'); });
    selectedIndex = index;
    if (items[index]) {
      items[index].classList.add('active');
    }
  }

  // ── Fermeture au clic extérieur ───────────────────────────────────────────

  document.addEventListener('click', function (e) {
    const container = document.getElementById('searchContainer');
    if (container && !container.contains(e.target)) {
      closeDropdown();
    }
  });

  function closeDropdown() {
    dropdown.classList.add('d-none');
    dropdown.innerHTML = '';
    suggestions = [];
    selectedIndex = -1;
  }

  // ── Utilitaires ───────────────────────────────────────────────────────────

  function escHtml(str) {
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
  }

  // ── Styles injectés dynamiquement ─────────────────────────────────────────

  const style = document.createElement('style');
  style.textContent = [
    '.search-topbar { position: relative; }',
    '.search-dropdown {',
    '  position: absolute; top: calc(100% + 4px); right: 0; min-width: 340px;',
    '  background: var(--bs-body-bg); border: 1px solid var(--bs-border-color);',
    '  border-radius: 8px; box-shadow: 0 8px 24px rgba(0,0,0,.3); z-index: 9999;',
    '  overflow: hidden; max-height: 300px; overflow-y: auto;',
    '}',
    '.search-item {',
    '  display: flex; align-items: center; gap: 8px; padding: 10px 14px;',
    '  cursor: pointer; border-bottom: 1px solid var(--bs-border-color); font-size: 13px;',
    '  transition: background .1s;',
    '}',
    '.search-item:last-child { border-bottom: none; }',
    '.search-item:hover, .search-item.active { background: rgba(var(--bs-primary-rgb),.12); }',
    '.search-code { font-family: monospace; color: var(--bs-primary); font-weight: 600; min-width: 90px; }',
    '.search-nom { flex: 1; }',
    '.search-res { font-family: monospace; font-size: 11px; color: var(--bs-warning); }',
  ].join('\n');
  document.head.appendChild(style);
})();
