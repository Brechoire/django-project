(() => {
  'use strict';
  document.getElementById('theme-toggle')?.addEventListener('click', () => {
    const dark = document.documentElement.classList.toggle('dark');
    try { localStorage.setItem('dpm-theme', dark ? 'dark' : 'light'); } catch (_) {}
  });
  // Aucune injection HTML côté client : les fragments sont rendus et échappés par Django.
  let dragged = null;
  document.addEventListener('dragstart', (event) => {
    if (event.target.closest('select, input, button, a')) { event.preventDefault(); return; }
    const card = event.target.closest('.card[draggable="true"]');
    if (!card) return;
    dragged = card; card.classList.add('dragging');
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('text/plain', card.dataset.taskId);
  });
  document.addEventListener('dragend', () => {
    dragged?.classList.remove('dragging'); dragged = null;
    document.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
  });
  document.addEventListener('dragover', (event) => {
    const column = event.target.closest('.column');
    if (column && dragged) { event.preventDefault(); column.classList.add('drag-over'); }
  });
  document.addEventListener('dragleave', (event) => {
    const column = event.target.closest('.column');
    if (column && !column.contains(event.relatedTarget)) column.classList.remove('drag-over');
  });
  document.addEventListener('drop', (event) => {
    const column = event.target.closest('.column');
    if (!column || !dragged) return;
    event.preventDefault(); column.classList.remove('drag-over');
    const token = dragged.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (!token || !window.htmx) return;
    const url = new URL(dragged.dataset.moveUrl, window.location.origin);
    url.search = window.location.search;
    window.htmx.ajax('POST', url.pathname + url.search, {target: '#board-content', swap: 'innerHTML',
      values: {status: column.dataset.status, csrfmiddlewaretoken: token}});
  });
  document.addEventListener('htmx:afterSwap', () => {
    const status = document.getElementById('interaction-status');
    if (status) status.textContent = 'Tableau actualisé.';
  });
  document.addEventListener('htmx:responseError', () => {
    const status = document.getElementById('interaction-status');
    if (status) { status.classList.remove('sr-only'); status.classList.add('message', 'error');
      status.textContent = 'La modification a échoué. Rechargez la page et vérifiez votre connexion et vos permissions.'; }
  });
  if (window.htmx) { window.htmx.config.allowEval = false; window.htmx.config.allowScriptTags = false;
    window.htmx.config.selfRequestsOnly = true; }
})();
