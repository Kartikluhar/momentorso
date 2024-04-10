// function mousemove(){
//     let cursor = document.getElementById('cursor')
//     window.addEventListener("mousemove",function(dets){
//         cursor.style.transform = `translate(${dets.clientX-7}px , ${dets.clientY-5}px)`
//         // console.log(dets)
//     })
// }

// mousemove()




// navbar effects
let navbar = document.getElementById("navbar");
let menu = document.getElementById("menu");
let viewportWidth = window.innerWidth || document.documentElement.clientWidth;
window.addEventListener("scroll",function(){
    if (document.documentElement.scrollTop > 70) {
        navbar.classList.add("sticky");
    }else{
        navbar.classList.remove("sticky");
    }
})

window.addEventListener("scroll",function(){
    if (document.documentElement.scrollTop > 70 && viewportWidth <= 900) {
        menu.classList.add("menu-scroll")
        menu.classList.add("menu-show-background1");
    }else if(document.documentElement.scrollTop < 70 && viewportWidth <= 900){
        menu.classList.remove("menu-scroll")
        menu.classList.remove("menu-show-background1");
    }
})

// Toggle Menu 

let flag = 0;
function toggleMenu(){
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