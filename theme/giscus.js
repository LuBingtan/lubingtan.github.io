// giscus — GitHub Discussions-based comments and reactions
(function() {
  const content = document.querySelector('main');
  if (!content) return;

  // Constrain giscus widget to content width
  const style = document.createElement('style');
  style.textContent = '#giscus-container { width:100%; max-width:100%; box-sizing:border-box; } #giscus-container iframe { width:100% !important; max-width:100% !important; }';
  document.head.appendChild(style);

  const container = document.createElement('div');
  container.id = 'giscus-container';
  container.style.marginTop = '3rem';
  container.style.paddingTop = '2rem';
  container.style.borderTop = '1px solid var(--border-color, #e0e0e0)';
  content.appendChild(container);

  const script = document.createElement('script');
  script.src = 'https://giscus.app/client.js';
  script.setAttribute('data-repo', 'lubingtan/lubingtan.github.io');
  script.setAttribute('data-repo-id', 'MDEwOlJlcG9zaXRvcnkzMjc1MTIzNzk=');
  script.setAttribute('data-category', 'General');
  script.setAttribute('data-category-id', 'DIC_kwDOE4VxO84C9b5K');
  script.setAttribute('data-mapping', 'title');
  script.setAttribute('data-strict', '0');
  script.setAttribute('data-reactions-enabled', '1');
  script.setAttribute('data-emit-metadata', '0');
  script.setAttribute('data-input-position', 'bottom');
  script.setAttribute('data-theme', 'light');
  script.setAttribute('data-lang', 'zh-CN');
  script.setAttribute('crossorigin', 'anonymous');
  script.async = true;
  container.appendChild(script);
})();
