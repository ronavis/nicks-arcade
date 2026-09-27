let arcadeData = [
    { title: "Asteroids", score: "8,560", initials: "COL" },
    { title: "BurgerTime", score: "15,100", initials: "NIC" },
    { title: "Bubble Bobble", score: "1,734,150", initials: "RJW" },
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
const storedData = localStorage.getItem('arcadeData');
if (storedData) {
    try { arcadeData = JSON.parse(storedData); } catch(e) {}
}

const listElement = document.getElementById('arcade-list');

// We append the QR section inside the list so it scrolls up too!
function renderList() {
    listElement.innerHTML = '';
    
    arcadeData.forEach(game => {
        const row = document.createElement('div');
        row.className = 'game-row';
        const imgName = game.title.toLowerCase().replace(/[^a-z0-9]/g, '') + '.png';
        const dateStr = game.date || "---";
        const proofHTML = game.proof ? `<span class="proof" data-proof="${game.proof}">VIEW PHOTO</span>` : '<span class="proof" style="color:#555; text-decoration:none; cursor:default;">---</span>';

        row.innerHTML = `
            <div class="marquee-container">
                <img src="images/${imgName}?v=2" class="marquee-image" alt="${game.title}" onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                <div class="marquee-text" style="display: none;">${game.title}</div>
            </div>
            <div class="score-col">
                <span class="score">${game.score}</span>
            </div>
            <div class="date-col">
                <span class="date">${dateStr}</span>
            </div>
            <div class="initials-col">
                <span class="initials">${game.initials}</span>
            </div>
            <div class="proof-col">
                ${proofHTML}
            </div>
        `;
        listElement.appendChild(row);
    });

    document.querySelectorAll('.proof[data-proof]').forEach(el => {
        el.addEventListener('click', (e) => {
            document.getElementById('photo-viewer-img').src = e.target.getAttribute('data-proof');
            document.getElementById('photo-modal').style.display = 'flex';
        });
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

// Photo Viewer Modal
const closePhotoBtn = document.getElementById('closePhotoBtn');
if (closePhotoBtn) {
    closePhotoBtn.addEventListener('click', () => {
        document.getElementById('photo-modal').style.display = 'none';
        document.getElementById('photo-viewer-img').src = '';
    });
}

// UI Settings Logic
const marqueeSizeSlider = document.getElementById('marqueeSizeSlider');
const marqueeSizeDisplay = document.getElementById('marqueeSizeDisplay');
const fontUpload = document.getElementById('fontUpload');
const resetFontBtn = document.getElementById('resetFontBtn');

const savedMarqueeSize = localStorage.getItem('arcade_marquee_size');
if(savedMarqueeSize && marqueeSizeSlider) {
    marqueeSizeSlider.value = savedMarqueeSize;
    marqueeSizeDisplay.innerText = savedMarqueeSize;
    document.documentElement.style.setProperty('--marquee-width', savedMarqueeSize + 'px');
    document.documentElement.style.setProperty('--marquee-height', (savedMarqueeSize * 0.3) + 'px');
}

const savedFont = localStorage.getItem('arcade_custom_font');
if(savedFont) applyCustomFont(savedFont);

if (marqueeSizeSlider) {
    marqueeSizeSlider.addEventListener('input', (e) => {
        const val = e.target.value;
        marqueeSizeDisplay.innerText = val;
        document.documentElement.style.setProperty('--marquee-width', val + 'px');
        document.documentElement.style.setProperty('--marquee-height', (val * 0.3) + 'px');
        localStorage.setItem('arcade_marquee_size', val);
    });
}

if (fontUpload) {
    fontUpload.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if(file) {
            const reader = new FileReader();
            reader.onload = (ev) => {
                applyCustomFont(ev.target.result);
                localStorage.setItem('arcade_custom_font', ev.target.result);
            };
            reader.readAsDataURL(file);
        }
    });
}

if (resetFontBtn) {
    resetFontBtn.addEventListener('click', () => {
        localStorage.removeItem('arcade_custom_font');
        const styleEl = document.getElementById('customFontStyle');
        if(styleEl) styleEl.remove();
        fontUpload.value = '';
    });
}

function applyCustomFont(dataUrl) {
    let styleEl = document.getElementById('customFontStyle');
    if(!styleEl) {
        styleEl = document.createElement('style');
        styleEl.id = 'customFontStyle';
        document.head.appendChild(styleEl);
    }
    styleEl.innerHTML = `
        @font-face {
            font-family: 'CustomScoreFont';
            src: url(${dataUrl});
        }
        :root {
            --font-score: 'CustomScoreFont', monospace;
        }
    `;
}

// Tabs Logic
const tabs = document.querySelectorAll('.tab-btn');
tabs.forEach(tab => {
    tab.addEventListener('click', (e) => {
        document.querySelectorAll('.tab-btn').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(p => {
            p.classList.remove('active');
            p.style.display = 'none';
        });
        
        e.target.classList.add('active');
        if(e.target.id === 'tabScores') {
            document.getElementById('scoresPanel').style.display = 'block';
            document.getElementById('scoresPanel').classList.add('active');
        } else if(e.target.id === 'tabAdmins') {
            document.getElementById('adminsPanel').style.display = 'block';
            document.getElementById('adminsPanel').classList.add('active');
            renderAdminList();
        } else if(e.target.id === 'tabSettings') {
            document.getElementById('settingsPanel').style.display = 'block';
            document.getElementById('settingsPanel').classList.add('active');
        }
    });
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
    authorizedAdmins = ['ronavis@gmail.com']; // Master admin
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

// Resize image helper
function resizeImage(file, callback) {
    const reader = new FileReader();
    reader.onload = function(e) {
        const img = new Image();
        img.onload = function() {
            const canvas = document.createElement('canvas');
            const max_size = 800;
            let width = img.width;
            let height = img.height;
            if (width > height && width > max_size) {
                height *= max_size / width;
                width = max_size;
            } else if (height > max_size) {
                width *= max_size / height;
                height = max_size;
            }
            canvas.width = width;
            canvas.height = height;
            canvas.getContext('2d').drawImage(img, 0, 0, width, height);
            callback(canvas.toDataURL('image/jpeg', 0.8));
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

// Arcade Keyboard Logic
const chars = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','DEL','END'];
const keyboard = document.getElementById('arcade-keyboard');
let currentInitials = [];

function renderKeyboard() {
    keyboard.innerHTML = '';
    chars.forEach(c => {
        const btn = document.createElement('div');
        btn.className = 'key-btn';
        if(c === 'DEL') btn.classList.add('del');
        if(c === 'END') btn.classList.add('end');
        btn.innerText = c;
        btn.addEventListener('click', () => handleKey(c));
        keyboard.appendChild(btn);
    });
}

function updateInitialsDisplay() {
    for(let i=1; i<=3; i++) {
        const el = document.getElementById('char'+i);
        el.innerText = currentInitials[i-1] || '_';
        el.classList.remove('active');
    }
    if (currentInitials.length < 3) {
        document.getElementById('char' + (currentInitials.length + 1)).classList.add('active');
    }
    document.getElementById('new-initials').value = currentInitials.join('');
}

function handleKey(c) {
    if (c === 'DEL') {
        currentInitials.pop();
    } else if (c === 'END') {
        document.getElementById('submit-score').click();
    } else {
        if (currentInitials.length < 3) {
            currentInitials.push(c);
        }
    }
    updateInitialsDisplay();
}
renderKeyboard();

document.getElementById('submit-score').addEventListener('click', () => {
    if(!selectedGame) { alert("Select a game first!"); return; }
    const newScore = document.getElementById('new-score').value;
    const newInitials = document.getElementById('new-initials').value.toUpperCase();
    const proofFile = document.getElementById('new-proof').files[0];
    const msg = document.getElementById('adminMessage');
    
    if(newScore && newInitials.length > 0) {
        const formattedScore = parseInt(newScore.replace(/,/g, '')).toLocaleString();
        const dateStr = new Date().toLocaleDateString();
        
        const saveScore = (proofDataURL) => {
            selectedGame.score = formattedScore;
            selectedGame.initials = newInitials;
            selectedGame.date = dateStr;
            if(proofDataURL) selectedGame.proof = proofDataURL;
            
            localStorage.setItem('arcadeData', JSON.stringify(arcadeData));
            
            msg.innerText = "Score updated successfully!";
            msg.style.color = "#00ff00";
            
            setTimeout(() => {
                msg.innerText = '';
                searchInput.value = '';
                document.getElementById('new-score').value = '';
                document.getElementById('new-initials').value = '';
                currentInitials = [];
                updateInitialsDisplay();
                document.getElementById('new-proof').value = '';
                selectedGame = null;
            }, 1500);
            
            renderList();
            listElement.style.animationPlayState = 'paused';
        };

        if(proofFile) {
            msg.innerText = "Processing image...";
            msg.style.color = "#ffff00";
            resizeImage(proofFile, saveScore);
        } else {
            saveScore(null);
        }
    } else {
        msg.innerText = "Please enter a valid score and initials.";
        msg.style.color = "#ff0000";
    }
});
