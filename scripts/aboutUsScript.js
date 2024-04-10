
// about navbar effects

let aboutNavbar = document.getElementById("about-us-navbar");
let aboutMenuLinks = document.querySelectorAll(".menu-links")
window.addEventListener("scroll",function(){
    if (document.documentElement.scrollTop > 70) {
        aboutNavbar.classList.add("navbar-sticky");
        aboutMenuLinks.forEach(addclass => {
            addclass.classList.add("add-menu-link");
        })
        
    }else{
        aboutNavbar.classList.remove("navbar-sticky");
        aboutMenuLinks.forEach(addclass => {
            addclass.classList.remove("add-menu-link");
        })
    }
})


let navbar = document.getElementById("about-us-navbar");
let menu = document.getElementById("menu");
let toggleButton = document.getElementById("toggle-button");
let viewportWidth = window.innerWidth || document.documentElement.clientWidth;
window.addEventListener("scroll",function(){
    if (document.documentElement.scrollTop > 70 && viewportWidth <= 900) {
        menu.classList.add("about-menu-scroll")
        menu.classList.add("about-menu-show-background2");
        aboutMenuLinks.forEach(addclass => {
            addclass.classList.add("add-menu-link1");
        })
        toggleButton.classList.add("toggle-button-color");
        
    }else if(document.documentElement.scrollTop < 70 && viewportWidth <= 900){
        menu.classList.remove("about-menu-scroll")
        menu.classList.remove("about-menu-show-background2");
        aboutMenuLinks.forEach(addclass => {
            addclass.classList.remove("add-menu-link1");
        })
        toggleButton.classList.remove("toggle-button-color");
    }
})

let flag = 0;
function abouttoggleMenu(){
    if (flag == 0) {
        menu.classList.add("menu-show");
        menu.classList.remove("menu-hide");
        flag = 1;
    }else{
        menu.classList.remove("menu-show");
        menu.classList.add("menu-hide");
        flag = 0;
    }
}