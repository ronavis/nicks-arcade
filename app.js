let arcadeData = [
    { title: "Asteroids", score: "8,560", initials: "COL" },
    { title: "BurgerTime", score: "15,100", initials: "NIC" },
    { title: "Bust-A-Move", score: "1,734,150", initials: "RJW" },
    { title: "Centipede", score: "17,609", initials: "BMH" },
    { title: "Crystal Castles", score: "51,070", initials: "MAR" },
    { title: "Dig Dug", score: "31,700", initials: "MBW" },
    { title: "Donkey Kong", score: "16,200", initials: "RON" },
    { title: "Donkey Kong Junior", score: "21,700", initials: "NIC" },
    { title: "Donkey Kong 3", score: "44,400", initials: "MAR" },
    { title: "Dragon's Lair", score: "33,272", initials: "RON" },
    { title: "Frogger", score: "7,480", initials: "NIC" },
    { title: "Galaga", score: "41,510", initials: "JJH" },
    { title: "Gauntlet II", score: "10,800", initials: "MBW" },
    { title: "Mappy", score: "22,060", initials: "RON" },
    { title: "Ms. Pac-Man", score: "131,170", initials: "RON" },
    { title: "Pac-Land", score: "68,880", initials: "NIC" },
    { title: "Pac-Man", score: "85,500", initials: "NIC" },
    { title: "Pac-Mania", score: "89,880", initials: "MBW" },
    { title: "Pengo", score: "16,030", initials: "MBW" },
    { title: "Q*bert", score: "48,930", initials: "NIC" },
    { title: "Shinobi", score: "32,430", initials: "RON" },
    { title: "Space Invaders", score: "2,710", initials: "RON" },
    { title: "Star Wars", score: "791,088", initials: "NIC" },
    { title: "Street Fighter", score: "224,100", initials: "NIC" },
    { title: "Street Fighter II The World Warrior", score: "864,000", initials: "NIC" },
    { title: "Street Fighter II Champion Edition", score: "692,000", initials: "NIC" },
    { title: "Street Fighter II Hyper Fighting", score: "662,000", initials: "NIC" },
    { title: "VS. Excitebike", score: "1:02:30", initials: "RON" },
    { title: "The Goonies", score: "27,930", initials: "NIC" },
    { title: "Super Mario Bros.", score: "230,450", initials: "NIC" },
    { title: "Super Mario Bros. 3", score: "47,090", initials: "SLK" },
    { title: "Tetris", score: "38,921", initials: "MAR" }
];

const listElement = document.getElementById('arcade-list');

// We append the QR section inside the list so it scrolls up too!
function renderList() {
    listElement.innerHTML = '';
    
    arcadeData.forEach(game => {
        const row = document.createElement('div');
        row.className = 'game-row';
        const imgName = game.title.toLowerCase().replace(/[^a-z0-9]/g, '') + '.png';

        row.innerHTML = `
            <div class="marquee-container">
                <img src="images/${imgName}" class="marquee-image" alt="${game.title}" onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                <div class="marquee-text" style="display: none;">${game.title}</div>
            </div>
            <div class="score-col">
                <span class="col-label">SCORE</span>
                <span class="score">${game.score}</span>
            </div>
            <div class="initials-col">
                <span class="col-label">INITIALS</span>
                <span class="initials">${game.initials}</span>
            </div>
        `;
        listElement.appendChild(row);
    });

    const qrSection = document.createElement('div');
    qrSection.className = 'qr-section';
    qrSection.innerHTML = `
        <p>SCAN TO LOGIN<br>& ENTER SCORES</p>
        <div id="qrcode"></div>
    `;
    listElement.appendChild(qrSection);

    // Generate QR Code pointing to this page with a login hash
    new QRCode(document.getElementById("qrcode"), {
        text: window.location.href.split('#')[0] + "#login",
        width: 150,
        height: 150,
        colorDark : "#000000",
        colorLight : "#ffffff",
        correctLevel : QRCode.CorrectLevel.H
    });
    
    // Clicking the QR code simulates scanning it on the same device
    document.getElementById("qrcode").addEventListener('click', () => {
        window.location.hash = "login";
        checkLoginHash();
    });
}

renderList();

// Modal Logic
const modal = document.getElementById('admin-modal');
const closeBtn = document.querySelector('.close-btn');
const loginBtn = document.getElementById('google-login-btn');
const loginView = document.getElementById('login-view');
const adminView = document.getElementById('admin-view');

function checkLoginHash() {
    if(window.location.hash === "#login") {
        // Pause crawl animation while modal is open
        listElement.style.animationPlayState = 'paused';
        modal.style.display = "flex";
        loginView.style.display = "block";
        adminView.style.display = "none";
    }
}
window.addEventListener('hashchange', checkLoginHash);
checkLoginHash();

closeBtn.addEventListener('click', () => {
    modal.style.display = "none";
    window.location.hash = "";
    listElement.style.animationPlayState = 'running';
});

loginBtn.addEventListener('click', () => {
    // Simulate Google Login for admins "Nick" or "Ron"
    const user = prompt("Google Sign-In Simulation:\\n\\nEnter your email (e.g., nick@gmail.com or ron@gmail.com):");
    if(user && (user.toLowerCase().startsWith("nick") || user.toLowerCase().startsWith("ron"))) {
        alert("Welcome Admin!");
        loginView.style.display = "none";
        adminView.style.display = "block";
    } else if (user) {
        alert("Access Denied. Admins only.");
        modal.style.display = "none";
        window.location.hash = "";
        listElement.style.animationPlayState = 'running';
    }
});

// Search functionality
const searchInput = document.getElementById('game-search');
const searchResults = document.getElementById('search-results');
let selectedGame = null;

searchInput.addEventListener('input', (e) => {
    const val = e.target.value.toLowerCase();
    searchResults.innerHTML = '';
    selectedGame = null;
    if(!val) {
        searchResults.style.display = 'none';
        return;
    }
    
    const matches = arcadeData.filter(g => g.title.toLowerCase().includes(val));
    if (matches.length > 0) {
        searchResults.style.display = 'block';
    } else {
        searchResults.style.display = 'none';
    }
    
    matches.forEach(g => {
        const div = document.createElement('div');
        div.className = 'search-item';
        div.innerText = g.title;
        div.addEventListener('click', () => {
            searchInput.value = g.title;
            selectedGame = g;
            searchResults.innerHTML = '';
            searchResults.style.display = 'none';
        });
        searchResults.appendChild(div);
    });
});

document.getElementById('submit-score').addEventListener('click', () => {
    if(!selectedGame) { alert("Select a game first!"); return; }
    const newScore = document.getElementById('new-score').value;
    const newInitials = document.getElementById('new-initials').value.toUpperCase();
    
    if(newScore && newInitials.length > 0) {
        // Simple regex to add commas to number if they didn't
        const formattedScore = parseInt(newScore.replace(/,/g, '')).toLocaleString();
        selectedGame.score = formattedScore;
        selectedGame.initials = newInitials;
        alert("Score updated successfully!");
        
        // Reset form
        searchInput.value = '';
        document.getElementById('new-score').value = '';
        document.getElementById('new-initials').value = '';
        selectedGame = null;
        
        // Close modal and re-render
        modal.style.display = "none";
        window.location.hash = "";
        renderList();
        listElement.style.animationPlayState = 'running';
    } else {
        alert("Please enter a valid score and initials.");
    }
});
