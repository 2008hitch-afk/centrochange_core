// Accessibility and wording for Frappe's native form; no credential handling.
function enhanceLogin() {
  if (document.body.dataset.path !== 'login') return;
  for (const logo of document.querySelectorAll('.page-card-head .app-logo')) {
    logo.alt = 'Centro Change';
    logo.width = 44;
    logo.height = 44;
  }
  for (const title of document.querySelectorAll('.page-card-head h4')) {
    const heading = document.createElement('h1');
    heading.className = title.className;
    heading.replaceChildren(...title.childNodes);
    title.replaceWith(heading);
  }
  for (const toggle of document.querySelectorAll('.toggle-password')) {
    const input = document.querySelector(toggle.getAttribute('toggle'));
    if (!input) continue;
    toggle.setAttribute('role', 'button');
    toggle.setAttribute('tabindex', '0');
    const update = () => {
      const shown = input.type === 'text';
      toggle.setAttribute('aria-label', shown ? 'Nascondi password' : 'Mostra password');
      toggle.setAttribute('aria-pressed', String(shown));
    };
    toggle.addEventListener('click', () => queueMicrotask(update));
    toggle.addEventListener('keydown', event => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        toggle.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
      }
    });
    update();
  }
  const translate = () => {
    for (const title of document.querySelectorAll('.login-error-banner .es-alert__title')) {
      if (title.textContent.trim() === 'Invalid credentials, try again.' ||
          title.textContent.trim() === 'Invalid login credentials') {
        title.textContent = 'Credenziali non valide. Controlla email e password e riprova.';
      }
    }
  };
  translate();
  for (const banner of document.querySelectorAll('.login-error-banner')) {
    new MutationObserver(translate).observe(banner, { childList: true, characterData: true, subtree: true });
  }
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', enhanceLogin, { once: true });
else enhanceLogin();
