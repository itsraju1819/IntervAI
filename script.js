// ===============================
// IntervAI Landing Page
// ===============================


// Get buttons
const startBtn = document.getElementById("startBtn");
const navStartBtn = document.getElementById("navStartBtn");
const ctaStartBtn = document.getElementById("ctaStartBtn");


// Function for starting the interview
function startInterview() {

    window.location.href = "pages/setup.html";

}


// Add click events
startBtn.addEventListener("click", startInterview);

navStartBtn.addEventListener("click", startInterview);

ctaStartBtn.addEventListener("click", startInterview);