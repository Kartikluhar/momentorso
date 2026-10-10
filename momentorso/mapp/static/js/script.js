document.addEventListener("DOMContentLoaded", function() {
  const menuBtn = document.getElementById("menuBtn");
  const mobileMenu = document.getElementById("mobileMenu");
  const menuIcon = document.getElementById("menuIcon");

  // Prevent errors if elements don't exist on page
  if (!menuBtn || !mobileMenu || !menuIcon) return;

  let isOpen = false;

  menuBtn.addEventListener("click", () => {
    isOpen = !isOpen;

    // Slide animation
    mobileMenu.classList.toggle("translate-x-full");

    // Icon change
    menuIcon.innerText = isOpen ? "close" : "menu";

    // Disable scroll
    document.body.style.overflow = isOpen ? "hidden" : "auto";
  });
});
