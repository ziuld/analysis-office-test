// Trusted navigation only; repository and model text is always escaped by the renderer.
(() => {
  function reveal(id) {
    let target;
    try { target = document.getElementById(decodeURIComponent(id)); } catch { return; }
    if (!target) return;
    for (let node = target; node; node = node.parentElement) {
      if (node.tagName === 'DETAILS') node.open = true;
    }
    requestAnimationFrame(() => target.scrollIntoView({block: 'start'}));
  }
  document.addEventListener('click', event => {
    const anchor = event.target.closest && event.target.closest('a[href^="#"]');
    if (anchor) reveal(anchor.getAttribute('href').slice(1));
  });
  window.addEventListener('hashchange', () => reveal(location.hash.slice(1)));
  if (location.hash) reveal(location.hash.slice(1));
})();
