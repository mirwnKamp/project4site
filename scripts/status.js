// Live server status for the home page. Reads status.json next to the page; the game VPS writes it every minute
// (tools/vps/p4-site-status). No file or bad data: the [data-live] blocks stay hidden.
// Shape: {"updated": 1795335063, "game": true, "login": true, "bosses": [{"name": "Antharas", "state": "alive"|"dead"|"busy"}]}
(function () {
  if (!window.fetch || !document.querySelector('[data-live]')) return;
  var STATES = { alive: 'Alive', dead: 'Dead', busy: 'In battle / waiting' };
  var text = function (el, s) { if (el) el.textContent = s; };

  fetch('status.json', { cache: 'no-store' }).then(function (r) {
    if (!r.ok) throw new Error(r.status);
    return r.json();
  }).then(function (s) {
    if (typeof s.game !== 'boolean' || !Array.isArray(s.bosses)) return;
    var up = s.game && s.login !== false;
    text(document.querySelector('[data-status-game]'), up ? 'Online' : 'Offline');
    var dot = document.querySelector('[data-status-dot]');
    if (dot) dot.classList.add(up ? 'is-up' : 'is-down');

    var grid = document.querySelector('[data-status-bosses]');
    if (grid) {
      s.bosses.forEach(function (b) {
        var state = STATES[b.state] ? b.state : 'busy';
        var card = document.createElement('div');
        card.className = 'p4-boss p4-frame';
        var name = document.createElement('span');
        name.className = 'p4-boss__name';
        name.textContent = String(b.name);
        var chip = document.createElement('span');
        chip.className = 'p4-boss__state is-' + state;
        chip.textContent = STATES[state];
        card.appendChild(name);
        card.appendChild(chip);
        grid.appendChild(card);
      });
    }
    if (s.updated) {
      var mins = Math.max(0, Math.round((Date.now() / 1000 - s.updated) / 60));
      text(document.querySelector('[data-status-updated]'), 'Live from the server · updated ' + (mins < 1 ? 'just now' : mins + ' min ago'));
    }
    document.querySelectorAll('[data-live]').forEach(function (el) {
      if (el.matches('.p4-bosses') && !s.bosses.length) return;
      el.hidden = false;
    });
  }).catch(function () { /* no live data here (e.g. GitHub Pages): keep the static page */ });
})();
