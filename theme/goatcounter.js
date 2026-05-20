// GoatCounter — page views + per-page counter display
// Requires "Allow adding visitor counts on your website" enabled in GoatCounter settings.
(function() {
  var script = document.createElement('script');
  script.src = 'https://gc.zgo.at/count.js';
  script.setAttribute('data-goatcounter', 'https://lubingtan.goatcounter.com/count');
  script.async = true;

  script.onload = function() {
    if (!window.goatcounter || !window.goatcounter.visit_count) return;
    window.goatcounter.visit_count({
      append: 'main',
      type: 'html',
      no_branding: true,
    });
  };

  document.head.appendChild(script);
})();
