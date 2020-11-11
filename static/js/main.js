// Manipulating the Logo in home_welcome.html
const logo = document.querySelectorAll('#logo path');

console.log(logo);

for(let i = 20; i < logo.length; i++){
    console.log(`Letter ${i} is ${logo[i].getTotalLength()}`);
}

function delay(n) {
    n = n || 2000;
    return new Promise((done) => {
        setTimeout(() => {
            done();
        }, n);
    });
}

// BARBAJS
/*
function pageTransition() {
    var tl = gsap.timeline();
    tl.to(".loading-screen", {
        duration: 1.2,
        width: "100%",
        left: "0%",
        ease: "Expo.easeInOut",
    });

    tl.to(".loading-screen", {
        duration: 1,
        width: "100%",
        left: "100%",
        ease: "Expo.easeInOut",
        delay: 0.3,
    });
    tl.set(".loading-screen", { left: "-100%" });
}

function contentAnimation() {
    var tl = gsap.timeline();
    tl.from(".animate-this-button", { duration: 1, y: 25, opacity: 0, stagger: 0.4, delay: 0.2});
}


$(function () {
    barba.init({
        sync: true,

        transitions: [
            {
                async leave(data) {
                    const done = this.async();

                    pageTransition();
                    await delay(1000);
                    done();
                },

                async enter(data) {
                    contentAnimation();
                },

                async once(data) {
                    contentAnimation();
                },
            },
        ],
    });
});

barba.hooks.afterEnter((data) => {

});
*/
