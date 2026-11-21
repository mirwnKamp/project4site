// Opening countdown. Markup: <div class="header__content-timer" data-open="2026-12-20T20:00:00+02:00" data-end-msg="...">
// The date is ISO 8601 with the server's UTC offset. Empty or invalid date: the timer stays hidden.
document.querySelectorAll('.header__content-timer[data-open]').forEach(function (box) {
  var open = Date.parse(box.getAttribute('data-open'));
  if (isNaN(open)) return;
  var time = box.querySelector('.header__content-timer-time');
  var nums = box.querySelectorAll('.header__content-timer-time-num');
  var pad = function (n) { return n < 10 ? '0' + n : String(n); };
  box.hidden = false;
  function tick() {
    var left = Math.floor((open - Date.now()) / 1000);
    if (left <= 0) {
      clearInterval(timer);
      time.innerHTML = '<div class="header__content-timer-time-end flex-cc">' + (box.getAttribute('data-end-msg') || 'SERVER IS ONLINE!') + '</div>';
      return;
    }
    var parts = [Math.floor(left / 86400), Math.floor(left / 3600) % 24, Math.floor(left / 60) % 60, left % 60];
    parts.forEach(function (v, i) {
      var text = i ? pad(v) : String(v), el = nums[i];
      if (el.textContent === text) return;
      el.textContent = text;
      el.classList.remove('p4-tick'); void el.offsetWidth; el.classList.add('p4-tick'); // restart the tick animation (ui.css)
    });
  }
  var timer = setInterval(tick, 1000);
  tick();
});
