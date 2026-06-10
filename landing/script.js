const header = document.querySelector(".site-header");

function syncHeader() {
  header.dataset.elevated = window.scrollY > 16 ? "true" : "false";
}

syncHeader();
window.addEventListener("scroll", syncHeader, { passive: true });
