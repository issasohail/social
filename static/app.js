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
})();
