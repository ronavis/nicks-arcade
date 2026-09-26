const arcadeData = [
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

const grid = document.getElementById('arcade-grid');

arcadeData.forEach(game => {
    const card = document.createElement('div');
    card.className = 'game-card';

    // Image integration is prepared. For now it uses neon styled text for the marquees.
    card.innerHTML = `
        <div class="marquee-container">
            <img src="images/${game.title.toLowerCase().replace(/[^a-z0-9]/g, '')}.jpg" class="marquee-image" alt="${game.title}" onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
            <div class="marquee-text" style="display: none;">${game.title}</div>
        </div>
        <div class="score-row">
            <span class="initials">${game.initials}</span>
            <span class="score">${game.score}</span>
        </div>
    `;
    grid.appendChild(card);
});
