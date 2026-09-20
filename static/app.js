(() => {
  const getCookie = (name) => document.cookie.split('; ').find((row) => row.startsWith(`${name}=`))?.split('=')[1];
  const csrfToken = decodeURIComponent(getCookie('csrftoken') || '');

  document.querySelectorAll('.inline-edit').forEach((field) => {
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
