// Minimal deck controller: keyboard/click navigation, hash deep links, stage scaling.
// Keys: Right/PageDown/Space/Enter = next, Left/PageUp/Backspace = prev,
// Home/End = first/last, F = fullscreen. Slides marked data-skip are hidden.
(function () {
  "use strict";
  var stage = document.querySelector(".stage");
  var slides = Array.prototype.slice.call(document.querySelectorAll(".slide:not([data-skip])"));
  Array.prototype.forEach.call(document.querySelectorAll(".slide[data-skip]"), function (el) {
    el.remove();
  });
  var counter = document.querySelector("[data-counter]");
  var progress = document.querySelector(".progress");
  var index = 0;

  function pad(n) {
    return String(n).padStart(2, "0");
  }

  function fit() {
    var scale = Math.min(window.innerWidth / 1600, window.innerHeight / 900);
    stage.style.transform = "scale(" + scale + ")";
  }

  function show(next) {
    index = Math.max(0, Math.min(slides.length - 1, next));
    slides.forEach(function (el, n) {
      el.classList.toggle("is-active", n === index);
    });
    // Blue key slides need light chrome; let CSS switch it via a stage class.
    stage.classList.toggle("on-blue", slides[index].classList.contains("blue"));
    counter.textContent = pad(index + 1) + " / " + pad(slides.length);
    progress.style.width = ((index + 1) / slides.length) * 100 + "%";
    try {
      history.replaceState(null, "", "#" + (index + 1));
    } catch (err) {
      /* file:// in some browsers refuses replaceState; navigation still works */
    }
  }

  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(function () {});
    } else {
      document.exitFullscreen();
    }
  }

  document.addEventListener("keydown", function (event) {
    var key = event.key;
    if (key === "ArrowRight" || key === "PageDown" || key === " " || key === "Enter") {
      event.preventDefault();
      show(index + 1);
    } else if (key === "ArrowLeft" || key === "PageUp" || key === "Backspace") {
      event.preventDefault();
      show(index - 1);
    } else if (key === "Home") {
      show(0);
    } else if (key === "End") {
      show(slides.length - 1);
    } else if (key === "f" || key === "F") {
      toggleFullscreen();
    }
  });

  stage.addEventListener("click", function (event) {
    var rect = stage.getBoundingClientRect();
    show(event.clientX - rect.left > rect.width / 2 ? index + 1 : index - 1);
  });

  window.addEventListener("resize", fit);
  var start = parseInt((location.hash || "#1").slice(1), 10);
  fit();
  show(isNaN(start) ? 0 : start - 1);
})();
