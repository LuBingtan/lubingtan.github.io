// GoatCounter — privacy-friendly page view analytics + counter display
(function() {
  // Load GoatCounter
  var script = document.createElement('script');
  script.src = 'https://gc.zgo.at/count.js';
  script.setAttribute('data-goatcounter', 'https://lubingtan.goatcounter.com/count');
  script.async = true;
  document.head.appendChild(script);

  // Show page view count after GoatCounter loads
  script.onload = function() {
    if (!window.goatcounter || !window.goatcounter.count) return;
    window.goatcounter.count().then(function(n) {
      var main = document.querySelector('main');
      if (!main) return;
      var el = document.createElement('p');
      el.style.marginTop = '2rem';
      el.style.fontSize = '0.85rem';
      el.style.color = '#888';
      el.textContent = '📊 ' + (n || 0).toLocaleString() + ' views';
      main.appendChild(el);
    });
  };
})();
