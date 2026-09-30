(() => {
  const detail = document.querySelector('.harmony-detail');
  if (!detail || detail.querySelector('.photo-update-link')) return;
  const photo = detail.querySelector('.marriage-biodata-photo');
  if (!photo) return;
  if (photo.tagName === 'IMG') {
    photo.style.cursor = 'zoom-in'; photo.title = 'Open full-size photo';
    photo.addEventListener('click', () => window.open(photo.src, '_blank', 'noopener'));
  }
  const picker = document.createElement('input'); picker.type = 'file'; picker.accept = 'image/*'; picker.hidden = true;
  const upload = document.createElement('button'); upload.type = 'button'; upload.className = 'photo-update-link'; upload.textContent = 'Upload photo';
  upload.addEventListener('click', () => picker.click());
  picker.addEventListener('change', async () => {
    const file = picker.files?.[0]; if (!file) return;
    upload.disabled = true; upload.textContent = 'Uploading…';
    const csrf = document.cookie.split('; ').find(x => x.startsWith('csrftoken='))?.split('=')[1] || '';
    const profileId = location.pathname.match(/family-harmony\/(\d+)/)?.[1];
    const data = new FormData(); data.append('profile_id', profileId); data.append('photo', file); data.append('csrfmiddlewaretoken', csrf);
    const response = await fetch('/family-harmony/inline-update/', {method: 'POST', body: data});
    if (response.ok) {
      const url = URL.createObjectURL(file);
      if (photo.tagName === 'IMG') photo.src = url;
      else { const image = document.createElement('img'); image.className = photo.className; image.src = url; image.alt = 'Profile photo'; photo.replaceWith(image); }
      upload.textContent = 'Change photo';
    } else upload.textContent = 'Try again';
    upload.disabled = false;
  });
  photo.insertAdjacentElement('afterend', picker); picker.insertAdjacentElement('afterend', upload);
})();
