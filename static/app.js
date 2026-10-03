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
    if (select.dataset.searchEnhanced === '1') return;
    select.dataset.searchEnhanced = '1';
    const wrapper = document.createElement('div');
    wrapper.className = 'select2-lite';
    const input = document.createElement('input');
    input.type = 'search';
    input.className = 'select2-lite-input';
    input.placeholder = select.options[0]?.text || 'Search';
    input.autocomplete = 'off';
    const menu = document.createElement('div');
    menu.className = 'select2-lite-menu';
    const multiple = select.multiple;

    const syncInput = () => {
      if (multiple) {
        const selected = Array.from(select.selectedOptions).filter(o => o.value);
        input.value = '';
        input.placeholder = selected.length ? `${selected.length} selected — type to search` : (select.options[0]?.text || 'Type to search');
      } else {
        input.value = select.selectedIndex > 0 ? select.options[select.selectedIndex].text : '';
      }
    };

    Array.from(select.options).forEach((option) => {
      if (!option.value) return;
      const item = document.createElement('button');
      item.type = 'button';
      item.className = 'select2-lite-option';
      item.dataset.value = option.value;
      item.textContent = option.text;
      const syncSelected = () => item.classList.toggle('is-selected', option.selected);
      syncSelected();
      item.addEventListener('mousedown', (event) => event.preventDefault());
      item.addEventListener('click', () => {
        if (multiple) {
          option.selected = !option.selected;
          syncSelected();
          syncInput();
          select.dispatchEvent(new Event('change', {bubbles: true}));
          input.focus();
        } else {
          select.value = option.value;
          syncInput();
          menu.classList.remove('is-open');
          select.dispatchEvent(new Event('change', {bubbles: true}));
        }
      });
      menu.appendChild(item);
    });
    select.parentNode.insertBefore(wrapper, select);
    wrapper.appendChild(input);
    wrapper.appendChild(menu);
    wrapper.appendChild(select);
    select.classList.add('select2-native');
    syncInput();
    const openMenu = () => {
      menu.classList.add('is-open');
      window.setTimeout(() => input.focus(), 0);
    };
    input.addEventListener('focus', openMenu);
    input.addEventListener('click', openMenu);
    input.addEventListener('input', () => {
      const needle = input.value.toLowerCase();
      menu.classList.add('is-open');
      menu.querySelectorAll('.select2-lite-option').forEach((item) => {
        item.hidden = !item.textContent.toLowerCase().includes(needle);
      });
    });
    select.addEventListener('change', () => {
      syncInput();
      if (multiple) {
        Array.from(select.options).forEach((option) => {
          if (!option.value) return;
          const item = menu.querySelector(`.select2-lite-option[data-value="${CSS.escape(option.value)}"]`);
          if (item) item.classList.toggle('is-selected', option.selected);
        });
      }
    });
    document.addEventListener('click', (event) => {
      if (!wrapper.contains(event.target)) menu.classList.remove('is-open');
    });
  });
})();

/* Compact public marriage form action: open, copy, or WhatsApp share. */
(() => {
  document.querySelectorAll('.public-marriage-actions').forEach(group => {
    let invitation;
    const getInvitation = async () => {
      if (!invitation) invitation = fetch(group.dataset.invitationUrl, {headers: {'Accept': 'application/json'}}).then(async response => {
        if (!response.ok) throw new Error('Could not create public form link');
        return response.json();
      });
      return invitation;
    };
    group.querySelectorAll('[data-public-form-action]').forEach(button => button.addEventListener('click', async () => {
      const action = button.dataset.publicFormAction;
      const previous = button.textContent;
      button.disabled = true;
      try {
        const links = await getInvitation();
        if (action === 'open') window.open(links.public_url, '_blank', 'noopener');
        if (action === 'whatsapp') window.open(links.whatsapp_url, '_blank', 'noopener');
        if (action === 'copy') {
          if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(links.public_url);
          else { const input = document.createElement('textarea'); input.value = links.public_url; document.body.append(input); input.select(); document.execCommand('copy'); input.remove(); }
          button.textContent = '✓';
          window.setTimeout(() => { button.textContent = previous; }, 1200);
        }
      } catch (error) {
        button.textContent = '!';
        window.setTimeout(() => { button.textContent = previous; }, 1200);
      } finally { button.disabled = false; }
    }));
  });
})();

/* Family Harmony detail: turn displayed values into save-on-blur inline editors. */
(() => {
  const detail = document.querySelector('.harmony-detail');
  if (!detail) return;
  const fields = {
    'AGE / DOB': null, 'DATE OF BIRTH': 'person_date_of_birth', 'GENDER': 'person_gender', 'NATIONALITY': 'person_nationality', 'IDENTITY TYPE': 'person_identity_type', 'IDENTITY NUMBER': 'person_identity_number',
    'JAMATKHANA': null, 'LOCAL COUNCIL': null, 'REGIONAL COUNCIL': null,
    'MOBILE': 'person_mobile', 'EMAIL': 'person_email', 'CITY': 'person_city', 'COUNTRY': 'person_country', 'HEIGHT': 'height_cm', 'WEIGHT': 'weight_kg',
    'PHYSICAL STATUS': 'physical_status', 'DISABILITY': 'disability_status', 'KNOWN DISEASES': 'known_diseases', 'HEALTH': 'health_information', 'HEALTH NOTES': 'health_information',
    'FATHER': 'father_name', 'FATHER OCCUPATION': 'father_occupation', 'MOTHER': 'mother_name',
    'MOTHER OCCUPATION': 'mother_occupation', 'BROTHERS': 'brothers_count', 'SISTERS': 'sisters_count',
    'FAMILY RESIDENCE': 'family_residence', 'FAMILY TYPE': 'family_type', 'CASTE / TRIBE': 'caste_tribe',
    'FAMILY BACKGROUND': 'family_background', 'FAMILY VALUES': 'family_values', 'EDUCATION': 'education_level',
    'INSTITUTION': 'institution', 'PROFESSION': 'profession', 'EMPLOYER / BUSINESS': 'employer_or_business',
    'INCOME': 'income_range', 'LANGUAGES': 'languages', 'SMOKING': 'smoking', 'HOUSE': 'owns_house', 'CAR': 'owns_car', 'INTERESTS': 'interests',
    'PERSONAL STATEMENT': 'personal_statement', 'WILLING TO RELOCATE': 'person_willing_to_relocate'
  };
  const profileId = location.pathname.match(/family-harmony\/(\d+)/)?.[1];
  const csrf = document.cookie.split('; ').find(x => x.startsWith('csrftoken='))?.split('=')[1] || '';
  const optionNode = document.getElementById('harmony-inline-options');
  const options = optionNode ? JSON.parse(optionNode.textContent) : {};
  const multiFields = new Set(['disability_status', 'caste_tribe', 'known_diseases', 'languages', 'preference_preferred_education_options', 'preference_preferred_professions']);
  const typeableFields = new Set(['profession']);
  const headerRows = detail.querySelectorAll('.harmony-head-contact span');
  if (headerRows[0]) {
    const line = headerRows[0].textContent; const dob = (line.match(/DOB:\s*([^·]+)/) || [,'—'])[1].trim();
    const match = line.match(/Height \/ Weight:\s*(\d+)\s*cm\s*\/\s*([^\s]+)\s*kg/);
    const badges = [`<b class="harmony-pill">${dob}</b>`];
    if (match) { const inches = Math.round(Number(match[1]) / 2.54); badges.push(`<b class="harmony-pill">${Math.floor(inches / 12)} ft ${inches % 12} in</b>`, `<b class="harmony-pill">${match[2]} kg</b>`); }
    headerRows[0].innerHTML = badges.join('');
  }
  if (headerRows[1]) {
    const place = headerRows[1].textContent.replace(/^City \/ Country:\s*/, '').split('/').map(x => x.trim()).filter(Boolean);
    headerRows[1].innerHTML = place.map(x => `<b class="harmony-pill">${x}</b>`).join('');
    headerRows[0]?.parentNode.insertBefore(headerRows[1], headerRows[0]);
  }
  detail.querySelectorAll('.biodata-item').forEach(item => {
    const label = item.querySelector('small')?.textContent.trim().toUpperCase();
    const preferenceSection = item.closest('.biodata-section')?.querySelector('h2')?.textContent.includes('Preferences');
    const preferenceMap = {'MIN AGE':'preference_minimum_age','MAX AGE':'preference_maximum_age','EDUCATION':'preference_preferred_education_options','PROFESSION':'preference_preferred_professions','LOCATION':'preference_preferred_cities','INCOME':'preference_preferred_income_options','WILLING TO RELOCATE':'preference_willingness_to_relocate'};
    const value = item.querySelector('strong'); const field = preferenceSection ? preferenceMap[label] : fields[label];
    if (!field || !value || value.querySelector('a')) return;
    value.classList.add('inline-value'); value.title = 'Click to edit';
    value.addEventListener('click', () => {
      if (value.querySelector('input, select, button')) return;
      const original = value.textContent.trim() === '—' ? '' : value.textContent.trim();
      const choices = options[field] || [];
      if (multiFields.has(field)) {
        const selected = original.split(',').map(x => x.trim()).filter(Boolean);
        const box = document.createElement('div'); box.className = 'inline-multi-editor'; value.classList.add('is-editing');
        choices.forEach(choice => { const label = document.createElement('label'); const check = document.createElement('input'); check.type = 'checkbox'; check.value = choice; check.checked = selected.includes(choice); label.append(check, document.createTextNode(` ${choice}`)); box.append(label); });
        const close = () => { value.classList.remove('is-editing'); value.textContent = original || '—'; };
        const outside = event => { if (!box.contains(event.target)) { close(); document.removeEventListener('click', outside, true); } };
        const apply = document.createElement('button'); apply.type = 'button'; apply.textContent = 'Apply'; box.append(apply); value.replaceChildren(box);
        setTimeout(() => document.addEventListener('click', outside, true), 0);
        apply.onclick = async () => { const chosen = [...box.querySelectorAll('input:checked')].map(x => x.value).join(', '); const form = new FormData(); form.append('profile_id', profileId); form.append('field', field); form.append('value', chosen); form.append('csrfmiddlewaretoken', csrf); const response = await fetch('/family-harmony/inline-update/', {method: 'POST', body: form}); document.removeEventListener('click', outside, true); value.classList.remove('is-editing'); value.textContent = response.ok ? (chosen || '—') : (original || '—'); };
        return;
      }
      const input = choices.length && !typeableFields.has(field) ? document.createElement('select') : document.createElement('input');
      if (choices.length && typeableFields.has(field)) {
        const listId = `harmony-${field}-options`;
        let list = document.getElementById(listId);
        if (!list) { list = document.createElement('datalist'); list.id = listId; choices.forEach(choice => { const option = document.createElement('option'); option.value = choice; list.append(option); }); document.body.append(list); }
        input.setAttribute('list', listId); input.value = original;
      } else if (choices.length) {
        input.add(new Option('Select…', ''));
        choices.forEach(choice => input.add(new Option(choice, choice, false, choice === original)));
      } else input.value = original;
      value.replaceChildren(input); input.focus();
      const finish = async save => {
        if (!save) { value.textContent = original || '—'; return; }
        const form = new FormData(); form.append('profile_id', profileId); form.append('field', field); form.append('value', input.value); form.append('csrfmiddlewaretoken', csrf);
        const response = await fetch('/family-harmony/inline-update/', {method: 'POST', body: form});
        value.textContent = response.ok ? (input.value || '—') : (original || '—');
      };
      if (input.tagName === 'SELECT') { input.addEventListener('change', () => finish(true), {once: true}); setTimeout(() => input.addEventListener('blur', () => finish(true), {once: true}), 120); }
      else input.addEventListener('blur', () => finish(true), {once: true});
      input.addEventListener('keydown', event => { if (event.key === 'Enter') { event.preventDefault(); finish(true); } if (event.key === 'Escape') finish(false); });
    });
  });
})();
