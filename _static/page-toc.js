// Right-hand "On this page" behavior, book-wide.
document.addEventListener("DOMContentLoaded", () => {
  // The theme's scrollspy marks anything in the top 40% of the viewport
  // active, which lands on the NEXT section once headings sit close
  // together; tighten the zone. This runs before Bootstrap reads the
  // attribute (DOMContentLoaded vs. window load).
  document.body.setAttribute("data-bs-root-margin", "0px 0px -86%");

  // A click should highlight its own entry, instantly — the spy re-marks
  // every section the smooth scroll passes, and bottom-of-page sections
  // never reach the active zone at all. So: set the clicked entry active
  // right away and pin it until the scroll settles; the observer corrects
  // the spy's mid-flight updates before paint, so nothing flashes.
  const sidebar = document.querySelector(".bd-sidebar-secondary");
  const links = sidebar ? [...sidebar.querySelectorAll("a[href^='#']")] : [];
  let pin = null;
  const release = () => {
    if (!pin) return;
    pin.observer.disconnect();
    clearTimeout(pin.timer);
    pin = null;
  };
  links.forEach((link) => {
    link.addEventListener("click", () => {
      release();
      const assert = () => links.forEach((a) => a.classList.toggle("active", a === link));
      assert();
      const observer = new MutationObserver(() => {
        const active = sidebar.querySelectorAll("a.active");
        if (active.length !== 1 || active[0] !== link) assert();
      });
      observer.observe(sidebar, { subtree: true, attributeFilter: ["class"] });
      let done = false;
      const finish = () => {
        if (done) return;
        done = true;
        setTimeout(release, 150);
      };
      window.addEventListener("scrollend", finish, { once: true });
      pin = { observer, timer: setTimeout(finish, 2000) };
    });
  });

  // The {schedule} directive emits hidden anchor sections so the week bands
  // appear in the menu; move each id onto its band row so the links scroll
  // to the week itself.
  const table = document.querySelector("table.sched-table");
  if (!table) return;
  const bands = [...table.querySelectorAll("tbody tr")].filter((tr) =>
    tr.querySelector(":scope > td:first-child > p > strong")
  );
  document.querySelectorAll("section.sched-anchor").forEach((stub, i) => {
    if (bands[i]) {
      bands[i].id = stub.id;
      stub.removeAttribute("id");
    }
  });
  // A direct #week-N visit scrolled before the ids moved; scroll again.
  if (location.hash) {
    const target = document.getElementById(location.hash.slice(1));
    if (target) target.scrollIntoView();
  }
});
