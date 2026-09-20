(() => {
  const getCookie = (name) => document.cookie.split('; ').find((row) => row.startsWith(`${name}=`))?.split('=')[1];
  const csrfToken = decodeURIComponent(getCookie('csrftoken') || '');

  const bindInlineEditors = (root = document) => root.querySelectorAll('.inline-edit').forEach((field) => {
    let savedValue = field.value;
    const save = async () => {
      if (field.value === savedValue) return;
      field.classList.remove('inline-error');
      field.classList.add('inline-saving');
      try {
        const response = await fetch(field.dataset.inlineUrl, {
          method: 'POST',
          headers: {'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': csrfToken},
          body: new URLSearchParams({
            id: field.dataset.recordId,
            field: field.dataset.inlineField,
            value: field.value,
          }),
        });
        if (!response.ok) throw new Error('Update failed');
        savedValue = field.value;
        field.classList.remove('inline-saving');
        field.classList.add('inline-saved');
        window.setTimeout(() => field.classList.remove('inline-saved'), 900);
      } catch (error) {
        field.classList.remove('inline-saving');
        field.classList.add('inline-error');
        field.value = savedValue;
      }
    };
    field.addEventListener('blur', save);
    field.addEventListener('change', save);
  });
  bindInlineEditors();

  const filterForms = document.querySelectorAll('.ajax-filter-form');
  filterForms.forEach((form) => {
    let timer;
    const refresh = async () => {
      const params = new URLSearchParams(new FormData(form));
      params.delete('page');
      const url = `${window.location.pathname}?${params.toString()}`;
      const response = await fetch(url, {headers: {'X-Requested-With': 'XMLHttpRequest'}});
      if (!response.ok) return;
      const html = await response.text();
      const documentFragment = new DOMParser().parseFromString(html, 'text/html');
      const currentResults = document.querySelector('.list-results');
      const nextResults = documentFragment.querySelector('.list-results');
      if (!currentResults || !nextResults) return;
      currentResults.replaceWith(nextResults);
      bindInlineEditors(nextResults);
      window.history.replaceState({}, '', url);
      document.querySelectorAll('.export-link').forEach((link) => {
        const exportParams = new URLSearchParams(new FormData(form));
        exportParams.set('format', link.dataset.exportFormat);
        link.href = `${window.location.pathname}?${exportParams.toString()}`;
      });
    };
    const schedule = () => {
      window.clearTimeout(timer);
      timer = window.setTimeout(() => refresh().catch(() => {}), 250);
    };
    form.addEventListener('submit', (event) => {
      event.preventDefault();
      refresh().catch(() => {});
    });
    form.querySelectorAll('select, input').forEach((field) => {
      field.addEventListener(field.tagName === 'INPUT' ? 'input' : 'change', schedule);
    });
  });

  document.addEventListener('click', (event) => {
    const link = event.target.closest('.list-results .pagination a');
    if (!link || !document.querySelector('.ajax-filter-form')) return;
    event.preventDefault();
    fetch(link.href, {headers: {'X-Requested-With': 'XMLHttpRequest'}})
      .then((response) => response.text())
      .then((html) => {
        const nextResults = new DOMParser().parseFromString(html, 'text/html').querySelector('.list-results');
        const currentResults = document.querySelector('.list-results');
        if (nextResults && currentResults) {
          currentResults.replaceWith(nextResults);
          bindInlineEditors(nextResults);
          window.history.replaceState({}, '', link.href);
        }
      })
      .catch(() => {});
  });

  document.querySelectorAll('select[data-searchable="true"]').forEach((select) => {
    const wrapper = document.createElement('div');
    wrapper.className = 'select2-lite';
    const input = document.createElement('input');
    input.type = 'search';
    input.className = 'select2-lite-input';
    input.placeholder = select.options[0]?.text || 'Search';
    input.value = select.selectedIndex > 0 ? select.options[select.selectedIndex].text : '';
    input.autocomplete = 'off';
    const menu = document.createElement('div');
    menu.className = 'select2-lite-menu';
    Array.from(select.options).forEach((option) => {
      if (!option.value) return;
      const item = document.createElement('button');
      item.type = 'button';
      item.className = 'select2-lite-option';
      item.dataset.value = option.value;
      item.textContent = option.text;
      item.addEventListener('mousedown', (event) => event.preventDefault());
      item.addEventListener('click', () => {
        select.value = option.value;
        input.value = option.text;
        menu.classList.remove('is-open');
        select.dispatchEvent(new Event('change', {bubbles: true}));
      });
      menu.appendChild(item);
    });
    select.parentNode.insertBefore(wrapper, select);
    wrapper.appendChild(input);
    wrapper.appendChild(menu);
    wrapper.appendChild(select);
    select.classList.add('select2-native');
    input.addEventListener('focus', () => menu.classList.add('is-open'));
    input.addEventListener('input', () => {
      const needle = input.value.toLowerCase();
      menu.classList.add('is-open');
      menu.querySelectorAll('.select2-lite-option').forEach((item) => {
        item.hidden = !item.textContent.toLowerCase().includes(needle);
      });
    });
    document.addEventListener('click', (event) => {
      if (!wrapper.contains(event.target)) menu.classList.remove('is-open');
    });
  });
})();
