// Prevent accidental double submissions while a local launch is being requested.
document.querySelectorAll('.action-list form').forEach((form) => {
  form.addEventListener('submit', () => {
    const button = form.querySelector('button');
    button.disabled = true;
    button.setAttribute('aria-busy', 'true');
  });
});
window.addEventListener('pageshow', () => {
  // Restore controls when Back/Forward restores a cached page.
  document.querySelectorAll('.action-list button').forEach((button) => {
    button.disabled = false;
    button.removeAttribute('aria-busy');
  });
});
