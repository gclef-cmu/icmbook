// Minimal play/pause controller for inline `.audio-chip` buttons (emitted by
// the {audio} role in _ext/icm_audio.py). Each chip lazily creates its Audio
// element on first click; starting one pauses any other that's playing. The
// `is-playing` class drives the play/pause icon swap (see _static/custom.css).
(function () {
  "use strict";

  function init() {
    var playing = null; // the Audio currently playing, if any

    document.querySelectorAll(".audio-chip").forEach(function (chip) {
      var src = chip.getAttribute("data-audio-src");
      if (!src) return;
      var audio = null;

      chip.addEventListener("click", function () {
        if (!audio) {
          audio = new Audio(src);
          audio.preload = "metadata";
          audio.addEventListener("play", function () {
            if (playing && playing !== audio) playing.pause();
            playing = audio;
            chip.classList.add("is-playing");
          });
          var clear = function () {
            chip.classList.remove("is-playing");
            if (playing === audio) playing = null;
          };
          audio.addEventListener("pause", clear);
          audio.addEventListener("ended", clear);
        }
        if (audio.paused) audio.play();
        else audio.pause();
      });
    });
  }

  if (document.readyState !== "loading") init();
  else document.addEventListener("DOMContentLoaded", init);
})();
