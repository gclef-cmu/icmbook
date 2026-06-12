// Minimal play/pause controller for `.audio-chip` buttons (emitted by the
// {audio} role + directive in _ext/icm_audio.py). Each chip lazily creates its
// Audio on first click; starting one pauses any other that's playing. The
// `is-playing` class drives the play/pause icon swap, and the `.acr-fill`
// progress ring tracks playback position (see _static/custom.css).
//
// Chips created after page load (live-cells.js builds them for audio that
// code cells produce) are wired through window.icmWireAudioChip, so every
// chip on the page shares the same exclusive-playback state.
(function () {
  "use strict";

  var playing = null; // the Audio currently playing, if any

  function wire(chip) {
    if (chip.dataset.acWired) return; // idempotent: safe to call twice
    var src = chip.getAttribute("data-audio-src");
    if (!src) return;
    chip.dataset.acWired = "1";
    var fill = chip.querySelector(".acr-fill"); // progress ring arc
    var audio = null;
    var raf = null;

    function setRing(offset) {
      if (fill) fill.style.strokeDashoffset = String(offset);
    }
    // Drive the ring on every animation frame (~60fps) rather than the
    // audio `timeupdate` event (which only fires ~4×/s and looks chunky).
    function loop() {
      if (audio.duration)
        setRing(100 - (audio.currentTime / audio.duration) * 100);
      raf = requestAnimationFrame(loop);
    }
    function stopLoop() {
      if (raf) cancelAnimationFrame(raf);
      raf = null;
    }

    chip.addEventListener("click", function () {
      if (!audio) {
        audio = new Audio(src);
        audio.preload = "metadata";
        audio.addEventListener("play", function () {
          if (playing && playing !== audio) playing.pause();
          playing = audio;
          chip.classList.add("is-playing");
          stopLoop();
          loop();
        });
        audio.addEventListener("pause", function () {
          chip.classList.remove("is-playing");
          if (playing === audio) playing = null;
          stopLoop();
        });
        audio.addEventListener("ended", function () {
          chip.classList.remove("is-playing");
          if (playing === audio) playing = null;
          stopLoop();
          setRing(100); // reset the ring to empty
        });
      }
      if (audio.paused) audio.play();
      else audio.pause();
    });
  }

  window.icmWireAudioChip = wire;

  function init() {
    document.querySelectorAll(".audio-chip").forEach(wire);
  }

  if (document.readyState !== "loading") init();
  else document.addEventListener("DOMContentLoaded", init);
})();
