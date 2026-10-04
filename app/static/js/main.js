(function () {
  'use strict';

  // ---- قائمة التنقل في الجوال ----
  var toggle = document.querySelector('.nav-toggle');
  var menu = document.getElementById('nav-menu');

  if (toggle && menu) {
    var setOpen = function (open) {
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      menu.classList.toggle('is-open', open);
    };

    toggle.addEventListener('click', function () {
      setOpen(toggle.getAttribute('aria-expanded') !== 'true');
    });

    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
        setOpen(false);
        toggle.focus();
      }
    });

    window.matchMedia('(min-width: 768px)').addEventListener('change', function (e) {
      if (e.matches) { setOpen(false); }
    });
  }

  // ---- حالة التحميل عند إرسال النماذج ----
  var resetButtons = function () {
    document.querySelectorAll('form[data-loading] button[type="submit"]').forEach(function (button) {
      button.disabled = false;
      button.removeAttribute('aria-busy');
      if (button.dataset.originalText) { button.textContent = button.dataset.originalText; }
    });
  };

  document.querySelectorAll('form[data-loading]').forEach(function (form) {
    form.addEventListener('submit', function () {
      var button = form.querySelector('button[type="submit"]');
      if (!button || button.disabled) { return; }
      button.dataset.originalText = button.textContent;
      button.setAttribute('aria-busy', 'true');
      button.textContent = button.dataset.loadingText || button.textContent;
      // تعطيل الزر بعد بدء الإرسال لمنع الضغط المزدوج
      window.setTimeout(function () { button.disabled = true; }, 0);
    });
  });

  // عند الرجوع للصفحة من الذاكرة المؤقتة للمتصفح
  window.addEventListener('pageshow', function (event) {
    if (event.persisted) { resetButtons(); }
  });
})();
