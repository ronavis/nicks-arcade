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
const settingsBtn = document.getElementById('settingsBtn');
const loginView = document.getElementById('login-view');
const adminView = document.getElementById('admin-view');

// Tabs Logic
const tabScores = document.getElementById('tabScores');
const tabAdmins = document.getElementById('tabAdmins');
const scoresPanel = document.getElementById('scoresPanel');
const adminsPanel = document.getElementById('adminsPanel');

tabScores.addEventListener('click', () => {
    tabScores.classList.add('active');
    tabAdmins.classList.remove('active');
    scoresPanel.classList.add('active');
    scoresPanel.style.display = 'block';
    adminsPanel.classList.remove('active');
    adminsPanel.style.display = 'none';
});

tabAdmins.addEventListener('click', () => {
    tabAdmins.classList.add('active');
    tabScores.classList.remove('active');
    adminsPanel.classList.add('active');
    adminsPanel.style.display = 'block';
    scoresPanel.classList.remove('active');
    scoresPanel.style.display = 'none';
    renderAdminList();
});


function openModal() {
    listElement.style.animationPlayState = 'paused';
    modal.style.display = "flex";
    
    // Check if already authenticated locally
    if (localStorage.getItem('arcade_admin_token')) {
        loginView.style.display = "none";
        adminView.style.display = "block";
    } else {
        loginView.style.display = "block";
        adminView.style.display = "none";
    }
}

function checkLoginHash() {
    if(window.location.hash === "#login") {
        openModal();
    }
}
window.addEventListener('hashchange', checkLoginHash);
checkLoginHash();

settingsBtn.addEventListener('click', () => {
    window.location.hash = "login";
    openModal();
});

closeBtn.addEventListener('click', () => {
    modal.style.display = "none";
    window.location.hash = "";
    listElement.style.animationPlayState = 'running';
});

// Load default admins
let authorizedAdmins = JSON.parse(localStorage.getItem('arcade_admins')) || [];
if (authorizedAdmins.length === 0) {
    authorizedAdmins = ['ron@gmail.com']; // Temporary master admin placeholder
    localStorage.setItem('arcade_admins', JSON.stringify(authorizedAdmins));
}

// Google Auth Callback
function handleCredentialResponse(response) {
    try {
        // Decode the JWT token to get the user's email
        const token = response.credential;
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));

        const payload = JSON.parse(jsonPayload);
        const userEmail = payload.email.toLowerCase();

        if (authorizedAdmins.includes(userEmail)) {
            // Success
            localStorage.setItem('arcade_admin_token', token);
            loginView.style.display = "none";
            adminView.style.display = "block";
        } else {
            // Unauthorized
            alert(`Access Denied. ${userEmail} is not an authorized admin.`);
        }
    } catch (e) {
        console.error("Authentication Error:", e);
        alert("Authentication failed.");
    }
}

// Manage Admins
function renderAdminList() {
    const adminListEl = document.getElementById('adminList');
    adminListEl.innerHTML = '';
    authorizedAdmins.forEach(email => {
        const li = document.createElement('li');
        li.innerHTML = `<span>${email}</span> <span class="remove-admin" data-email="${email}">[X]</span>`;
        adminListEl.appendChild(li);
    });
    
    document.querySelectorAll('.remove-admin').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const emailToRemove = e.target.getAttribute('data-email');
            if(authorizedAdmins.length === 1) {
                alert("Cannot remove the last admin!");
                return;
            }
            authorizedAdmins = authorizedAdmins.filter(a => a !== emailToRemove);
            localStorage.setItem('arcade_admins', JSON.stringify(authorizedAdmins));
            renderAdminList();
        });
    });
}

document.getElementById('submitAdmin').addEventListener('click', () => {
    const newAdmin = document.getElementById('newAdminEmail').value.trim().toLowerCase();
    const msg = document.getElementById('adminManageMessage');
    if (newAdmin && newAdmin.includes('@')) {
        if (!authorizedAdmins.includes(newAdmin)) {
            authorizedAdmins.push(newAdmin);
            localStorage.setItem('arcade_admins', JSON.stringify(authorizedAdmins));
            document.getElementById('newAdminEmail').value = '';
            msg.innerText = "Admin added successfully.";
            msg.style.color = "#00ff00";
            renderAdminList();
        } else {
            msg.innerText = "Admin already exists.";
            msg.style.color = "#ffff00";
        }
    } else {
        msg.innerText = "Invalid email address.";
        msg.style.color = "#ff0000";
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
    const msg = document.getElementById('adminMessage');
    
    if(newScore && newInitials.length > 0) {
        // Simple regex to add commas to number if they didn't
        const formattedScore = parseInt(newScore.replace(/,/g, '')).toLocaleString();
        selectedGame.score = formattedScore;
        selectedGame.initials = newInitials;
        
        msg.innerText = "Score updated successfully!";
        msg.style.color = "#00ff00";
        
        // Reset form
        setTimeout(() => {
            msg.innerText = '';
            searchInput.value = '';
            document.getElementById('new-score').value = '';
            document.getElementById('new-initials').value = '';
            selectedGame = null;
        }, 1500);
        
        // Re-render
        renderList();
        listElement.style.animationPlayState = 'paused';
    } else {
        msg.innerText = "Please enter a valid score and initials.";
        msg.style.color = "#ff0000";
    }
});
