  const menuBtn = document.getElementById("menuBtn");
  const mobileMenu = document.getElementById("mobileMenu");
  const menuIcon = document.getElementById("menuIcon");

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
