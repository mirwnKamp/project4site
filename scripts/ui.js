// Project4 UI layer (see ui.css): current page in the menu, tab strip behaviour, staggered content,
// race switching without page reloads, scroll reveal.
(function () {
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  // Pages are linked without ".html" (GitHub Pages serves /items as items.html). Names here are clean too.
  var clean = function (path) { var n = path.split('#')[0].split('?')[0].split('/').pop().replace(/\.html$/, ''); return n || 'index'; };
  var page = function () { return clean(location.pathname); };
  var racePages = ['class', 'elf', 'darkElf', 'orc', 'dwarf', 'kamael', 'ertheia', 'samurai', 'warg', 'shinemaker'];
  // Old links and bookmarks still open /items.html: show the clean address instead.
  if (/^https?:$/.test(location.protocol) && /\.html$/.test(location.pathname) && history.replaceState) {
    history.replaceState(history.state, '', location.pathname.replace(/index\.html$/, '').replace(/\.html$/, '') + location.search + location.hash);
  }
  // Same options wiki.js passes to the tab plugin; needed again when a race swaps in new tabs.
  var tabOptions = { classButton: 'wiki__nav-item', toggleClassButton: 'active', dataButtonAttr: 'data-open-tab', classBox: 'wiki__content',
    toggleClassBox: 'active', dataBoxAttr: 'data-name-tab', defaultElement: true, defaultIndexElement: 0, ancoreLinks: true };

  document.querySelectorAll('.nav__links-item').forEach(function (item, i) {
    item.style.setProperty('--i', i);
    var a = item.querySelector('a'), raw = a && a.getAttribute('href');
    if (!raw || /^(https?:)?\/\//.test(raw)) return;
    var href = clean(raw);
    if (href === page() || (href === 'class' && racePages.indexOf(page()) >= 0)) a.classList.add('is-current');
  });

  function scrollStrip(strip, el, smooth) {
    if (!el || strip.scrollWidth <= strip.clientWidth) return;
    var left = el.offsetLeft - (strip.clientWidth - el.offsetWidth) / 2;
    if (strip.scrollTo) strip.scrollTo({ left: left, behavior: smooth && !reduce ? 'smooth' : 'auto' }); else strip.scrollLeft = left;
  }

  // Phones/tablets: the tab strip is pinned with position:fixed while the tabs block is on screen. CSS sticky
  // jitters on iOS Safari while its toolbar hides/shows; fixed is drawn by the compositor and stays still.
  // Two observers (top spacer, end of the block): no scroll listener.
  var phone = window.matchMedia && matchMedia('(max-width: 1024px)');
  function pinNav(wiki, nav) {
    if (!phone || !('IntersectionObserver' in window)) return; // ui.css keeps position:sticky as the fallback
    document.documentElement.classList.add('p4-pin');
    // sentinel: zero height, marks where the strip starts; spacer: keeps its room while it is pinned.
    var sentinel = document.createElement('div'), spacer = document.createElement('div'), end = document.createElement('div');
    sentinel.className = 'p4-nav-sentinel';
    spacer.className = 'p4-nav-spacer';
    nav.parentNode.insertBefore(sentinel, nav);
    nav.parentNode.insertBefore(spacer, nav);
    (wiki.querySelector('.wiki__box') || wiki).appendChild(end);
    var above = false, endBelow = true;
    var place = function () {
      var on = phone.matches && above && endBelow;
      if (on) {
        var r = sentinel.getBoundingClientRect();
        spacer.style.height = nav.offsetHeight + 'px';
        nav.style.left = r.left + 'px';
        nav.style.width = r.width + 'px';
      } else {
        spacer.style.height = nav.style.left = nav.style.width = '';
      }
      nav.classList.toggle('is-pinned', on);
    };
    new IntersectionObserver(function (e) {
      above = e[0].boundingClientRect.top < 8;
      place();
    }, { rootMargin: '-8px 0px 0px 0px' }).observe(sentinel);
    new IntersectionObserver(function (e) {
      endBelow = e[0].isIntersecting || e[0].boundingClientRect.top > 0;
      place();
    }, { rootMargin: '-120px 0px 0px 0px' }).observe(end);
    window.addEventListener('resize', place);
  }

  // Tabs block (.wiki): staggered content and, on phones/tablets, the pinned tab strip.
  function initWiki(wiki) {
    // Icon rows (icon + loose text): wrap the text so CSS can centre it beside the icon.
    wiki.querySelectorAll('.wiki-icon-container').forEach(function (row) {
      if (row.querySelector(':scope > .p4-icon-text')) return;
      var text = document.createElement('div');
      text.className = 'p4-icon-text';
      Array.prototype.slice.call(row.childNodes).forEach(function (n) {
        if (!(n.nodeType === 1 && n.tagName === 'IMG')) text.appendChild(n);
      });
      row.appendChild(text);
      row.classList.add('p4-icon-row');
    });
    wiki.querySelectorAll('.wiki__content').forEach(function (tab) {
      tab.querySelectorAll(':scope > div[style] > div').forEach(function (el) { el.classList.add('p4-row'); });
      var items = tab.querySelectorAll('.p4-card, .wiki-icon-container, .wiki__content-main > table, .wiki__content-main > h3, .info-group, :scope > div[style] > div');
      items.forEach(function (el, i) { el.classList.add('p4-stagger'); el.style.setProperty('--i', Math.min(i, 12)); });
    });
    // Segment buttons inside a tab (items.html accessories: Right / Left slot): one grid at a time.
    wiki.querySelectorAll('.p4-seg').forEach(function (seg) {
      var show = function (name) {
        seg.querySelectorAll('button[data-seg]').forEach(function (b) {
          var on = b.getAttribute('data-seg') === name;
          b.classList.toggle('active', on);
          b.setAttribute('aria-selected', on ? 'true' : 'false');
        });
        seg.parentNode.querySelectorAll('[data-seg-panel]').forEach(function (p) { p.hidden = p.getAttribute('data-seg-panel') !== name; });
      };
      seg.querySelectorAll('button[data-seg]').forEach(function (b) { b.setAttribute('role', 'tab'); });
      show((seg.querySelector('button.active') || seg.querySelector('button[data-seg]')).getAttribute('data-seg'));
      seg.addEventListener('click', function (e) {
        var b = e.target.closest('button[data-seg]');
        if (b) show(b.getAttribute('data-seg'));
      });
    });
    var nav = wiki.querySelector('.wiki__nav');
    if (!nav) return;
    pinNav(wiki, nav);
    scrollStrip(nav, nav.querySelector('.wiki__nav-item.active'), false);
    nav.addEventListener('click', function (e) {
      var item = e.target.closest('.wiki__nav-item');
      if (!item) return;
      scrollStrip(nav, item, true);
      var box = wiki.querySelector('.wiki__box');
      if (!box || !/sticky|fixed/.test(getComputedStyle(nav).position)) return;
      var gap = box.getBoundingClientRect().top - nav.offsetHeight - 16;
      if (gap < 0) window.scrollBy({ top: gap, behavior: reduce ? 'auto' : 'smooth' });
    });
  }
  document.querySelectorAll('.wiki').forEach(initWiki);
  // Links to a tab on the same page (e.g. footer "game rules" -> wiki#rules while on the wiki) only change the hash.
  window.addEventListener('hashchange', function () {
    var id = decodeURIComponent(location.hash.slice(1));
    var btn = id && document.querySelector('.wiki__nav-item[data-open-tab="' + id.replace(/"/g, '') + '"]');
    if (btn && !btn.classList.contains('active')) btn.click();
  });

  // Race selector (Gameplay pages): an orange glider slides under the picked race and only the classes
  // below are swapped in from the other race page. Any failure falls back to a normal page load.
  var strip = document.querySelector('.race-strip');
  if (strip && window.fetch && window.DOMParser && history.pushState && window.jQuery) {
    var glider = document.createElement('span');
    glider.className = 'race-strip__glider';
    strip.insertBefore(glider, strip.firstChild);
    strip.classList.add('has-glider');
    var moveGlider = function (btn, animate) {
      if (!btn) return;
      glider.style.transition = animate && !reduce ? '' : 'none';
      glider.style.width = btn.offsetWidth + 'px';
      glider.style.height = btn.offsetHeight + 'px';
      glider.style.transform = 'translate(' + btn.offsetLeft + 'px,' + btn.offsetTop + 'px)';
    };
    var activeBtn = function () { return strip.querySelector('.race-btn.active'); };
    moveGlider(activeBtn(), false);
    scrollStrip(strip, activeBtn(), false);
    window.addEventListener('resize', function () { moveGlider(activeBtn(), false); });
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { moveGlider(activeBtn(), false); });

    var pages = {};
    var load = function (href) {
      return pages[href] || (pages[href] = fetch(href).then(function (r) {
        if (!r.ok) throw new Error(r.status);
        return r.text();
      }).then(function (html) { return new DOMParser().parseFromString(html, 'text/html'); })
        .catch(function (err) { delete pages[href]; throw err; }));
    };
    var wait = function (ms) { return new Promise(function (r) { setTimeout(r, reduce ? 0 : ms); }); };
    var busy = 0;

    var go = function (href, push) {
      var btn = strip.querySelector('.race-btn[href="' + href + '"]');
      if (!btn) { location.href = href; return; }
      var ticket = ++busy;
      strip.querySelectorAll('.race-btn').forEach(function (b) { b.classList.toggle('active', b === btn); b.removeAttribute('aria-current'); });
      btn.setAttribute('aria-current', 'page');
      moveGlider(btn, true);
      scrollStrip(strip, btn, true);
      var old = document.querySelector('.wiki');
      old.classList.add('p4-leave');
      Promise.all([load(href), wait(200)]).then(function (res) {
        if (ticket !== busy) return; // a newer click won
        var next = res[0].querySelector('.wiki');
        if (!next) throw new Error('no .wiki in ' + href);
        next = document.importNode(next, true);
        next.classList.add('p4-enter');
        if (push) history.pushState({ p4race: href }, '', href);
        old.parentNode.replaceChild(next, document.querySelector('.wiki'));
        jQuery(next).MVisionToggleClass(tabOptions);
        initWiki(next);
        var top = strip.getBoundingClientRect().top;
        if (top < 0) window.scrollBy({ top: top - 12, behavior: reduce ? 'auto' : 'smooth' });
      }).catch(function () { location.href = href; });
    };

    strip.addEventListener('click', function (e) {
      var a = e.target.closest('.race-btn');
      if (!a || e.metaKey || e.ctrlKey || e.shiftKey || e.button > 0) return;
      e.preventDefault();
      if (!a.classList.contains('active')) go(a.getAttribute('href'), true);
    });
    // Start loading a race as soon as a finger or pointer reaches its pill.
    ['pointerenter', 'touchstart', 'focusin'].forEach(function (type) {
      strip.addEventListener(type, function (e) {
        var a = e.target.closest && e.target.closest('.race-btn');
        if (a && !a.classList.contains('active')) load(a.getAttribute('href')).catch(function () {});
      }, { passive: true, capture: true });
    });
    history.replaceState({ p4race: page() }, '', location.href);
    // Back/forward: follow the URL (tab clicks add #hash entries without our state, so read the path).
    window.addEventListener('popstate', function () {
      var p = page(), cur = activeBtn();
      if (racePages.indexOf(p) >= 0 && cur && clean(cur.getAttribute('href')) !== p) go(p, false);
    });
  }

  // Sections fade up as they scroll into view.
  if (!reduce && 'IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
    }, { rootMargin: '0px 0px -8% 0px' });
    document.querySelectorAll('.section__title, .features .content-area, .information .col-1-4, .footer33').forEach(function (el, i) {
      if (el.querySelector('.race-strip')) return; // the race strip must not move
      el.classList.add('p4-reveal');
      el.style.transitionDelay = el.matches('.col-1-4') ? (i % 4) * 90 + 'ms' : '';
      io.observe(el);
    });
  }
})();
