

function darklightmode() {
    const logo = document.getElementById("logo");
    const currentSrc = logo.src.split("/").pop();

    if (currentSrc === "white%20w%20logo.png") {
        logo.src = "/logos/black w logo.png";
        document.documentElement.style.setProperty("--bg", "black");
        document.documentElement.style.setProperty("--card", "black");
        document.documentElement.style.setProperty("--text", "white");
        document.documentElement.style.setProperty("--nav", "black");
    } 
    
    else {
        logo.src = "/logos/white w logo.png";
        document.documentElement.style.setProperty("--bg", "white");
        document.documentElement.style.setProperty("--card", "white");
        document.documentElement.style.setProperty("--text", "black");
        document.documentElement.style.setProperty("--nav", "white");
    }

}


(() => {
  const track   = document.querySelector('.carousel__track');
  const slides  = Array.from(track.children);   // real slides only
  const slideW  = slides[0].offsetWidth + parseFloat(getComputedStyle(slides[0]).marginRight);
  let   index   = 1;                           // start on the *real* first slide

  const firstClone = slides[0].cloneNode(true);
  const lastClone  = slides[slides.length - 1].cloneNode(true);

  // Remove/replace IDs and hide from AT (assistive tech)
  firstClone.removeAttribute('id');
  lastClone.removeAttribute('id');
  firstClone.setAttribute('aria-hidden', 'true');
  lastClone.setAttribute('aria-hidden', 'true');


  track.append(firstClone);   // after last real slide
  track.prepend(lastClone);   // before first real slide

  // ---- Position the track on the true first slide ----
  track.style.transform = `translateX(${-slideW * index}px)`;

  // ----Navigation helpers (you can wire these to buttons) ----
  const move = step => {
    index += step;
    track.style.transition = 'transform 1s ease';
    track.style.transform = `translateX(${-slideW * index}px)`;
  };

  // ----Snap‑back when a clone is reached ----
  track.addEventListener('transitionend', () => {
    const all = Array.from(track.children);
    // The clones have `aria-hidden="true"` – a simple way to identify them
    if (all[index].hasAttribute('aria-hidden')) {
      // No animation for the jump
      track.style.transition = 'none';
      if (index === 0) {               // we’re on the *last* clone
        index = all.length - 2;        // point to the real last slide
      } else {                         // we’re on the *first* clone
        index = 1;                      // point to the real first slide
      }
      track.style.transform = `translateX(${-slideW * index}px)`;
      // Force a reflow so the next transition works
      void track.offsetWidth;
      track.style.transition = 'transform 1s ease';
    }
  });

  // ----Auto‑advance (optional) ----
  setInterval(() => move(0.01), 100);
})();