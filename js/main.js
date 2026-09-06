/* The Von Terra Project: nav + accordion behavior */
(function () {
  "use strict";

  var MOBILE = "(max-width: 768px)";
  function isMobile() { return window.matchMedia(MOBILE).matches; }

  // Mobile hamburger
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.querySelector(".site-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  var dropdowns = Array.prototype.slice.call(document.querySelectorAll(".dropdown"));

  function setOpen(dd, open) {
    dd.classList.toggle("open", open);
    var trigger = dd.querySelector("a.nav-link");
    if (trigger) trigger.setAttribute("aria-expanded", open ? "true" : "false");
  }

  function closeAll(except) {
    dropdowns.forEach(function (dd) { if (dd !== except) setOpen(dd, false); });
  }

  dropdowns.forEach(function (dd) {
    var trigger = dd.querySelector("a.nav-link");
    if (!trigger) return;

    // On mobile the first tap opens the submenu rather than navigating. The hub page stays
    // reachable because it is also the first link inside the submenu. Without that it was
    // unreachable on touch entirely.
    trigger.addEventListener("click", function (e) {
      if (isMobile()) {
        e.preventDefault();
        var open = !dd.classList.contains("open");
        closeAll(dd);
        setOpen(dd, open);
      }
      // Desktop: let the click through to the hub page.
    });

    // Keyboard: the CSS opens the menu on :focus-within, so this only needs to keep
    // aria-expanded truthful and let Escape dismiss without leaving the trigger.
    dd.addEventListener("focusin", function () { setOpen(dd, true); });
    dd.addEventListener("focusout", function () {
      // Defer: focusout fires before focusin on the next element.
      window.setTimeout(function () {
        if (!dd.contains(document.activeElement)) setOpen(dd, false);
      }, 0);
    });
    dd.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && dd.classList.contains("open")) {
        setOpen(dd, false);
        if (trigger) trigger.focus();
      }
    });
  });

  // Close open dropdowns when clicking outside. Applies on touch as well as desktop,
  // previously this bailed out on mobile, so a tapped-open menu stayed open indefinitely.
  document.addEventListener("click", function (e) {
    if (!e.target.closest(".dropdown")) closeAll(null);
  });

  // FAQ accordion
  document.querySelectorAll(".accordion-q").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var item = btn.closest(".accordion-item");
      var open = item.classList.toggle("open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    });
  });
})();
