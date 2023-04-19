// Initialize Modal scripts
function initializeBook() {
    let currentPage = 0;
    const pages = document.getElementsByClassName("book-page");

    function updatePageDisplay() {
        for (let i = 0; i < pages.length; i++) {
            pages[i].style.display = i === currentPage ? "block" : "none";
        }
    }

    function prevPage() {
        if (currentPage > 0) {
            currentPage--;
            updatePageDisplay();
        }
    }

    function nextPage() {
        if (currentPage < pages.length - 1) {
            currentPage++;
            updatePageDisplay();
        }
    }

    updatePageDisplay();

    window.prevPage = prevPage;
    window.nextPage = nextPage;
}

// Dark Mode Section
const darkModeToggle = document.getElementById("dark-mode-toggle");
const body = document.body;

// Load the user's dark mode preference from localStorage
const darkModePreference = localStorage.getItem("dark-mode");

// Apply the dark mode class if the user's preference is 'enabled'
if (darkModePreference === "enabled") {
    body.classList.add("dark-mode");

    darkModeToggle.textContent = "Light Mode";
} else {
    darkModeToggle.textContent = "Dark Mode";
}

// Toggle dark mode on button click
darkModeToggle.addEventListener("click", () => {
    body.classList.toggle("dark-mode");
    if (body.classList.contains("dark-mode")) {
        // Save the user's preference to localStorage
        localStorage.setItem("dark-mode", "enabled");
        darkModeToggle.textContent = "Light Mode";
    } else {
        localStorage.setItem("dark-mode", "disabled");
        darkModeToggle.textContent = "Dark Mode";
    }
});
