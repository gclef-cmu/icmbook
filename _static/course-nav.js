(function () {
  function setupCoursePartToggle() {
    const captions = document.querySelectorAll(".bd-sidebar-primary p.caption");
    const caption = Array.from(captions).find((node) => {
      const text = node.querySelector(".caption-text");
      return text && text.textContent.trim() === "Course Information";
    });

    if (!caption) {
      return;
    }

    const list = caption.nextElementSibling;
    if (!list || !list.matches("ul.bd-sidenav")) {
      return;
    }

    const text = caption.querySelector(".caption-text");
    const listId = "icm-course-sidebar-list";
    const storageKey = "icm-course-sidebar-expanded";
    const isCurrentSection = Boolean(list.querySelector(".current, .active"));
    const savedState = window.localStorage.getItem(storageKey);
    const startsExpanded = isCurrentSection || savedState === "true";

    list.id = listId;
    caption.classList.add("icm-collapsible-caption");
    caption.innerHTML = "";

    const button = document.createElement("button");
    button.type = "button";
    button.className = "icm-part-toggle";
    button.setAttribute("aria-controls", listId);

    const label = document.createElement("span");
    label.className = "caption-text";
    label.textContent = text.textContent.trim();

    const icon = document.createElement("span");
    icon.className = "toctree-toggle icm-part-toggle-icon";
    icon.setAttribute("role", "presentation");
    icon.setAttribute("aria-hidden", "true");

    const chevron = document.createElement("i");
    chevron.className = "fa-solid fa-chevron-down";
    icon.append(chevron);

    button.append(label, icon);
    caption.append(button);

    function setExpanded(expanded) {
      button.setAttribute("aria-expanded", String(expanded));
      list.hidden = !expanded;
    }

    setExpanded(startsExpanded);

    button.addEventListener("click", () => {
      const expanded = button.getAttribute("aria-expanded") !== "true";
      setExpanded(expanded);
      window.localStorage.setItem(storageKey, String(expanded));
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupCoursePartToggle);
  } else {
    setupCoursePartToggle();
  }
})();
