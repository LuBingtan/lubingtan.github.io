// GoatCounter — page views with subtle counter in bottom-right
// Requires "Allow adding visitor counts on your website" enabled in GoatCounter settings.
(function() {
  var script = document.createElement('script');
  script.src = 'https://gc.zgo.at/count.js';
  script.setAttribute('data-goatcounter', 'https://lubingtan.goatcounter.com/count');
  script.async = true;

  script.onload = function() {
    if (!window.goatcounter || !window.goatcounter.get_data) return;
    var path = window.goatcounter.get_data().p || location.pathname;
    fetch('https://lubingtan.goatcounter.com/counter/' + encodeURIComponent(path) + '.json')
      .then(function(r) { return r.json(); })
      .then(function(data) {
        var el = document.createElement('div');
        el.textContent = (data.count || '0').replace(/,/g, ',') + ' views';
        el.style.cssText = 'position:fixed;bottom:12px;right:16px;color:#bbb;font-size:12px;z-index:9999;pointer-events:none;';
        document.body.appendChild(el);
      })
      .catch(function() {}); // silently ignore if setting not enabled yet
  };

  document.head.appendChild(script);
})();
