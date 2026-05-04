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
