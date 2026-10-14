/* Bell Laundry & Cleaners — interactions and motion. No dependencies. */
(() => {
  'use strict';
  const doc = document.documentElement;
  doc.classList.add('js');
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const finePointer = matchMedia('(pointer: fine)').matches;
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  /* ---- split headings into words for the rise animation ---- */
  const splitWords = (el, delay = 0) => {
    if (el.dataset.splitDone) return;
    el.dataset.splitDone = '1';
    let i = 0;
    const walk = (node) => {
      [...node.childNodes].forEach((child) => {
        if (child.nodeType === 3) {
          const frag = document.createDocumentFragment();
          child.textContent.split(/(\s+)/).forEach((part) => {
            if (!part) return;
            if (/^\s+$/.test(part)) { frag.append(' '); return; }
            const w = document.createElement('span');
            w.className = 'w';
            w.innerHTML = '<span></span>';
            w.firstChild.textContent = part;
            w.firstChild.style.setProperty('--wi', i++);
            if (delay) w.firstChild.style.setProperty('--wd', delay + 's');
            frag.append(w);
          });
          child.replaceWith(frag);
        } else if (child.nodeType === 1 && !child.classList.contains('w')) {
          // keep styled spans (e.g. .script) but split their words too
          walk(child);
        }
      });
    };
    walk(el);
  };
  $$('[data-split]').forEach((el) => splitWords(el, parseFloat(el.dataset.split) || 0));
  $$('.slide-text h2').forEach((el) => splitWords(el, .15));

  /* ---- reveal on scroll ---- */
  $$('[data-stagger]').forEach((group) => {
    const step = parseFloat(group.dataset.stagger) || .08;
    [...group.children].forEach((child, i) => {
      if (!child.hasAttribute('data-reveal')) child.setAttribute('data-reveal', group.dataset.revealType || 'up');
      child.style.setProperty('--d', (i * step).toFixed(2) + 's');
    });
  });
  const revealables = $$('[data-reveal], [data-split], .timeline');
  if (reduce || !('IntersectionObserver' in window)) {
    revealables.forEach((el) => el.classList.add('is-in'));
  } else {
    // A fully clipped element never counts as intersecting, so clip reveals are
    // triggered by their (unclipped) parent instead.
    const targets = new Map();
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (!e.isIntersecting) return;
        (targets.get(e.target) || []).forEach((el) => el.classList.add('is-in'));
        io.unobserve(e.target);
      });
    }, { rootMargin: '0px 0px -10% 0px', threshold: 0 });
    revealables.forEach((el) => {
      const watch = (el.dataset.reveal || '').startsWith('clip') ? el.parentElement : el;
      if (!targets.has(watch)) targets.set(watch, []);
      targets.get(watch).push(el);
      io.observe(watch);
    });
  }

  /* ---- header: solid on scroll, hide while scrolling down ---- */
  const header = $('.header');
  const toTop = $('.to-top');
  let lastY = scrollY;
  let ticking = false;
  const onScroll = () => {
    const y = scrollY;
    if (header) {
      header.classList.toggle('is-scrolled', y > 10);
      const goingDown = y > lastY && y > 400;
      if (!doc.classList.contains('menu-open')) header.classList.toggle('is-hidden', goingDown);
    }
    if (toTop) {
      const max = doc.scrollHeight - innerHeight;
      toTop.classList.toggle('is-visible', y > 600);
      toTop.style.setProperty('--p', max > 0 ? (y / max).toFixed(3) : 0);
    }
    lastY = y;
    if (!reduce) { parallax(); steps(); yearFill(); }
    ticking = false;
  };
  addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });
  toTop?.addEventListener('click', () => scrollTo({ top: 0, behavior: reduce ? 'auto' : 'smooth' }));

  /* ---- parallax: [data-parallax="0.12"] slides its image (sized 120% in CSS) against the scroll,
     never further than the 10% overscan so no gap shows ---- */
  const parallaxEls = $$('[data-parallax]');
  function parallax() {
    const vh = innerHeight;
    parallaxEls.forEach((el) => {
      const r = el.getBoundingClientRect();
      if (r.bottom < -100 || r.top > vh + 100) return;
      const img = el.querySelector('img');
      if (!img) return;
      const speed = parseFloat(el.dataset.parallax) || .1;
      const limit = r.height * .1;
      const offset = Math.max(-limit, Math.min(limit, (r.top + r.height / 2 - vh / 2) * -speed));
      img.style.transform = `translate3d(0, ${offset.toFixed(1)}px, 0)`;
    });
  }

  /* ---- pickup steps: line grows with scroll, steps light up ---- */
  const stepsEl = $('.steps');
  const stepItems = stepsEl ? $$('.step', stepsEl) : [];
  function steps() {
    if (!stepsEl) return;
    const r = stepsEl.getBoundingClientRect();
    const mid = innerHeight * .6;
    const p = Math.min(1, Math.max(0, (mid - r.top) / r.height));
    stepsEl.style.setProperty('--progress', p.toFixed(3));
    stepItems.forEach((s) => s.classList.toggle('is-reached', s.getBoundingClientRect().top < mid));
  }

  /* ---- "1941" fills in as it crosses the viewport ---- */
  const years = $$('.year-big');
  function yearFill() {
    years.forEach((el) => {
      const r = el.getBoundingClientRect();
      const p = Math.min(1, Math.max(0, (innerHeight * .9 - r.top) / (innerHeight * .6)));
      el.style.setProperty('--fill', (p * 100).toFixed(1) + '%');
    });
  }
  if (reduce) years.forEach((el) => el.style.setProperty('--fill', '100%'));

  /* ---- hero slider ---- */
  const hero = $('.hero[data-slider]');
  if (hero) {
    const texts = $$('.slide-text', hero);
    const imgs = $$('.slide-img', hero);
    const tabs = $$('.slide-tab', hero);
    const dur = 7000;
    hero.style.setProperty('--slide-dur', dur + 'ms');
    let idx = 0;
    let timer;
    let remaining = dur;
    let started = Date.now();
    const show = (n) => {
      idx = (n + texts.length) % texts.length;
      [texts, imgs, tabs].forEach((list) => list.forEach((el, i) => {
        el.classList.toggle('is-active', i === idx);
        if (el.classList.contains('slide-text')) el.setAttribute('aria-hidden', i === idx ? 'false' : 'true');
        if (el.classList.contains('slide-text')) $$('a', el).forEach((a) => (a.tabIndex = i === idx ? 0 : -1));
      }));
      tabs.forEach((t, i) => t.setAttribute('aria-selected', i === idx ? 'true' : 'false'));
      // restart the tab progress animation
      const active = tabs[idx];
      if (active) { active.classList.remove('is-active'); void active.offsetWidth; active.classList.add('is-active'); }
      schedule(dur);
    };
    const schedule = (ms) => {
      clearTimeout(timer);
      if (reduce) return;
      remaining = ms;
      started = Date.now();
      timer = setTimeout(() => show(idx + 1), ms);
    };
    tabs.forEach((t, i) => t.addEventListener('click', () => show(i)));
    hero.addEventListener('mouseenter', () => { clearTimeout(timer); remaining -= Date.now() - started; hero.classList.add('is-paused'); });
    hero.addEventListener('mouseleave', () => { hero.classList.remove('is-paused'); schedule(Math.max(600, remaining)); });
    document.addEventListener('visibilitychange', () => { if (document.hidden) clearTimeout(timer); else schedule(dur); });
    show(0);

    // arch outline drifts against the pointer
    const outline = $('.arch-outline', hero);
    if (outline && finePointer && !reduce) {
      hero.addEventListener('pointermove', (e) => {
        const r = hero.getBoundingClientRect();
        const x = (e.clientX - r.left) / r.width - .5;
        const y = (e.clientY - r.top) / r.height - .5;
        outline.style.transform = `translate(${(-x * 18).toFixed(1)}px, ${(-y * 18).toFixed(1)}px)`;
      });
    }
  }

  /* ---- mobile menu ---- */
  const burger = $('.burger');
  const menu = $('.mobile-menu');
  const setMenu = (open) => {
    doc.classList.toggle('menu-open', open);
    burger?.setAttribute('aria-expanded', String(open));
    menu?.setAttribute('aria-hidden', String(!open));
    if (menu) menu.inert = !open;
    header?.classList.remove('is-hidden');
    if (open) menu?.querySelector('a')?.focus({ preventScroll: true });
  };
  if (menu) menu.inert = true;
  burger?.addEventListener('click', () => setMenu(!doc.classList.contains('menu-open')));
  menu?.addEventListener('click', (e) => { if (e.target.closest('a')) setMenu(false); });
  addEventListener('keydown', (e) => { if (e.key === 'Escape' && doc.classList.contains('menu-open')) { setMenu(false); burger?.focus(); } });
  addEventListener('resize', () => { if (innerWidth > 1024 && doc.classList.contains('menu-open')) setMenu(false); });

  /* ---- services dropdown (desktop): opens on hover/focus, the arrow toggles it for touch and keyboard ---- */
  $$('.has-menu').forEach((item) => {
    const btn = $('.menu-toggle', item);
    const set = (open) => {
      item.classList.toggle('is-open', open);
      item.classList.toggle('is-closed', !open && item.matches(':focus-within'));
      btn.setAttribute('aria-expanded', String(open));
    };
    btn.addEventListener('click', (e) => { e.stopPropagation(); set(!item.classList.contains('is-open')); });
    item.addEventListener('mouseleave', () => { item.classList.remove('is-closed'); });
    item.addEventListener('focusin', () => item.classList.remove('is-closed'));
    document.addEventListener('click', (e) => { if (!item.contains(e.target)) set(false); });
    item.addEventListener('keydown', (e) => { if (e.key === 'Escape') { set(false); btn.focus(); } });
  });
  /* mobile menu: expandable services list */
  $$('.has-sub').forEach((item) => {
    const btn = $('.sub-toggle', item);
    btn.addEventListener('click', () => {
      const open = !item.classList.contains('is-open');
      item.classList.toggle('is-open', open);
      btn.setAttribute('aria-expanded', String(open));
    });
  });

  /* ---- service card spotlight ---- */
  if (finePointer && !reduce) {
    $$('.svc-card').forEach((card) => card.addEventListener('pointermove', (e) => {
      const r = card.getBoundingClientRect();
      card.style.setProperty('--mx', `${e.clientX - r.left}px`);
      card.style.setProperty('--my', `${e.clientY - r.top}px`);
    }));
  }

  /* ---- magnetic buttons ---- */
  if (finePointer && !reduce) {
    $$('.btn').forEach((btn) => {
      btn.addEventListener('pointermove', (e) => {
        const r = btn.getBoundingClientRect();
        const x = e.clientX - r.left - r.width / 2;
        const y = e.clientY - r.top - r.height / 2;
        btn.style.transform = `translate(${(x * .12).toFixed(1)}px, ${(y * .22).toFixed(1)}px)`;
      });
      btn.addEventListener('pointerleave', () => { btn.style.transform = ''; });
    });
  }

  /* ---- FAQ: one open at a time, animated height ---- */
  $$('.faq').forEach((faq) => {
    const items = $$('details', faq);
    items.forEach((d) => {
      const summary = $('summary', d);
      const body = $('.answer', d);
      summary.addEventListener('click', (e) => {
        if (reduce || !body.animate) return; // native toggle
        e.preventDefault();
        const opening = !d.open;
        if (opening) {
          items.forEach((o) => { if (o !== d && o.open) close(o); });
          d.open = true;
          const h = body.offsetHeight;
          body.animate([{ height: '0px', opacity: 0 }, { height: h + 'px', opacity: 1 }], { duration: 450, easing: 'cubic-bezier(.22,1,.36,1)' });
        } else {
          close(d);
        }
      });
    });
    function close(d) {
      const body = $('.answer', d);
      const anim = body.animate([{ height: body.offsetHeight + 'px', opacity: 1 }, { height: '0px', opacity: 0 }], { duration: 350, easing: 'cubic-bezier(.65,0,.35,1)' });
      anim.onfinish = () => { d.open = false; };
    }
  });

  /* ---- open / closed status from the published store hours (Spartanburg time) ---- */
  const status = $$('[data-open-status]');
  if (status.length) {
    const parts = new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York', weekday: 'short', hour: 'numeric', minute: 'numeric', hour12: false })
      .formatToParts(new Date()).reduce((o, p) => (o[p.type] = p.value, o), {});
    const mins = (parseInt(parts.hour, 10) % 24) * 60 + parseInt(parts.minute, 10);
    const day = parts.weekday;
    const hours = { Mon: [450, 1080], Tue: [450, 1080], Wed: [450, 1080], Thu: [450, 1080], Fri: [450, 1080], Sat: [480, 720] };
    const today = hours[day];
    const open = today && mins >= today[0] && mins < today[1];
    status.forEach((el) => {
      el.classList.toggle('is-open', !!open);
      el.textContent = open ? (day === 'Sat' ? 'Open now · until noon' : 'Open now · until 6 p.m.') : 'Closed now';
    });
  }

  /* ---- forms: preview only, not connected to a mailbox yet ---- */
  $$('form[data-preview-form]').forEach((form) => {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      if (!form.reportValidity()) return;
      const note = $('.form-note', form);
      note?.classList.add('is-visible');
      note?.focus?.();
    });
  });

  /* ---- footer year ---- */
  $$('[data-year]').forEach((el) => (el.textContent = new Date().getFullYear()));

  onScroll();
})();
