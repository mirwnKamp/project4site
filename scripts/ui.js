// Project4 UI layer (see ui.css): current page in the menu, tab strip behaviour, staggered content, scroll reveal.
(function () {
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var page = location.pathname.split('/').pop() || 'index.html';
  var racePages = ['class.html', 'elf.html', 'darkElf.html', 'dwarf.html', 'orc.html'];

  document.querySelectorAll('.nav__links-item').forEach(function (item, i) {
    item.style.setProperty('--i', i);
    var a = item.querySelector('a'), href = a && (a.getAttribute('href') || '').split('/').pop();
    if (href && (href === page || (href === 'class.html' && racePages.indexOf(page) >= 0))) a.classList.add('is-current');
  });

  // Content of each tab animates in one piece after another when the tab opens.
  document.querySelectorAll('.wiki__content').forEach(function (tab) {
    var rows = tab.querySelectorAll(':scope > div[style] > div');
    rows.forEach(function (el) { el.classList.add('p4-row'); });
    var items = tab.querySelectorAll('.p4-card, .wiki-icon-container, .wiki__content-main > table, .wiki__content-main > h3, .info-group, :scope > div[style] > div');
    items.forEach(function (el, i) { el.classList.add('p4-stagger'); el.style.setProperty('--i', Math.min(i, 12)); });
  });

  // Phones/tablets: tabs are a sticky strip. Keep the picked pill centred and start the new tab from its top.
  function centre(nav, el, smooth) {
    if (nav.scrollWidth <= nav.clientWidth) return;
    var left = el.offsetLeft - (nav.clientWidth - el.offsetWidth) / 2;
    if (nav.scrollTo) nav.scrollTo({ left: left, behavior: smooth && !reduce ? 'smooth' : 'auto' }); else nav.scrollLeft = left;
  }
  document.querySelectorAll('.wiki__nav').forEach(function (nav) {
    var active = nav.querySelector('.wiki__nav-item.active');
    if (active) centre(nav, active, false);
    nav.addEventListener('click', function (e) {
      var item = e.target.closest('.wiki__nav-item');
      if (!item) return;
      centre(nav, item, true);
      var box = nav.parentElement.querySelector('.wiki__box');
      if (!box || getComputedStyle(nav).position !== 'sticky') return;
      var gap = box.getBoundingClientRect().top - nav.offsetHeight - 16;
      if (gap < 0) window.scrollBy({ top: gap, behavior: reduce ? 'auto' : 'smooth' });
    });
  });

  // Race strip (Gameplay pages): switching race keeps the visitor's place on the page and in the strip,
  // so only the content and the selected pill change (ui.css animates that with a view transition).
  var strip = document.querySelector('.race-strip');
  if (strip) {
    var key = 'p4-race-pos', saved = null;
    try { saved = JSON.parse(sessionStorage.getItem(key)); sessionStorage.removeItem(key); } catch (e) {}
    var current = strip.querySelector('.race-btn.active');
    var centreRace = function (smooth) {
      if (!current || strip.scrollWidth <= strip.clientWidth) return;
      var left = current.offsetLeft - (strip.clientWidth - current.offsetWidth) / 2;
      strip.scrollTo({ left: left, behavior: smooth && !reduce ? 'smooth' : 'auto' });
    };
    if (saved && racePages.indexOf(page) >= 0) {
      document.documentElement.classList.add('p4-same-section');
      strip.scrollLeft = saved.x;
      window.scrollTo(0, saved.y);
      setTimeout(function () { centreRace(true); }, 550);
    } else {
      centreRace(false);
    }
    strip.addEventListener('click', function (e) {
      var a = e.target.closest('.race-btn');
      if (!a || a.classList.contains('active')) { if (a) e.preventDefault(); return; }
      try { sessionStorage.setItem(key, JSON.stringify({ x: strip.scrollLeft, y: window.scrollY })); } catch (err) {}
    });
  }

  // Sections fade up as they scroll into view.
  if (!reduce && 'IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
    }, { rootMargin: '0px 0px -8% 0px' });
    document.querySelectorAll('.section__title, .features .content-area, .information .col-1-4, .footer33').forEach(function (el, i) {
      if (el.querySelector('.race-strip')) return; // the race strip must not move when switching race
      el.classList.add('p4-reveal');
      el.style.transitionDelay = el.matches('.col-1-4') ? (i % 4) * 90 + 'ms' : '';
      io.observe(el);
    });
  }
})();
