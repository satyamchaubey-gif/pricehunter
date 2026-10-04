document.addEventListener('DOMContentLoaded', () => {
    // 1. Custom Cursor Setup
    const cursor = document.querySelector('.cursor-follower');
    window.addEventListener('mousemove', (e) => {
        gsap.to(cursor, {
            x: e.clientX - 10,
            y: e.clientY - 10,
            duration: 0.1,
            ease: "power2.out"
        });
    });

    // 2. Initial Page Load Animation
    const tl = gsap.timeline();

    tl.from("nav", {
        y: -100,
        opacity: 0,
        duration: 1,
        ease: "power4.out"
    })
    .from(".eyebrow", {
        opacity: 0,
        y: 20,
        duration: 0.8,
        ease: "power3.out"
    }, "-=0.5")
    .from(".main-title", {
        opacity: 0,
        y: 30,
        duration: 1,
        ease: "power4.out"
    }, "-=0.6")
    .from(".hero-subtext", {
        opacity: 0,
        y: 20,
        duration: 0.8,
        ease: "power3.out"
    }, "-=0.7")
    .from(".search-wrapper", {
        opacity: 0,
        scale: 0.9,
        duration: 1,
        ease: "back.out(1.7)"
    }, "-=0.5");

    // Scan Line Animation
    gsap.to(".scan-line", {
        top: "100%",
        duration: 4,
        repeat: -1,
        ease: "linear"
    });

    // 3. Search Logic
    const searchBtn = document.getElementById('searchBtn');
    const autoHuntBtn = document.getElementById('autoHuntBtn');
    const productInput = document.getElementById('productInput');
    const resultsSection = document.getElementById('resultsSection');
    const resultsGrid = document.getElementById('resultsGrid');
    const resultTitle = document.getElementById('resultTitle');
    const loadingStatus = document.getElementById('loadingStatus');

    async function performSearch() {
        const query = productInput.value.trim();
        if (!query) {
            alert('Please enter a product name!');
            return;
        }

        // UI state: Transition to Results
        resultsSection.style.display = 'block';
        resultsGrid.innerHTML = '';
        resultTitle.innerText = 'Hunting for deals...';
        loadingStatus.innerText = "INITIALIZING SCAN...";

        try {
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}&num=20`);
            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            const results = data.results;
            if (results.length === 0) {
                resultTitle.innerText = "No targets found.";
                loadingStatus.innerText = "SCAN COMPLETE - NULL";
            } else {
                resultTitle.innerText = `FOUND ${results.length} MATCHES`;
                loadingStatus.innerText = "SCAN COMPLETE";

                // Build Cards
                results.forEach(item => {
                    const card = document.createElement('div');
                    card.className = 'card';
                    card.innerHTML = `
                        <span class="source">${item.source}</span>
                        <span class="price">${item.price_display}</span>
                        <div class="title">${item.title}</div>
                        <div class="card-actions" style="display: flex; gap: 10px; margin-top: auto;">
                            <a href="${item.url}" target="_blank" class="view-btn" style="flex: 1; text-align: center; text-decoration: none;">VIEW TARGET</a>
                            <button class="buy-btn" data-url="${item.url}" style="flex: 1; background: var(--highlight); color: var(--bg); border: none; padding: 12px; font-family: var(--font-mono); font-weight: 700; cursor: pointer; transition: 0.3s;">ADD TO CART</button>
                        </div>
                    `;
                    resultsGrid.appendChild(card);
                });

                // Kinetic Reveal Animation
                gsap.from(".card", {
                    opacity: 0,
                    y: 50,
                    stagger: 0.1,
                    duration: 0.8,
                    ease: "power3.out"
                });
            }
        } catch (error) {
            console.error('Search Error:', error);
            resultTitle.innerText = 'Scan Error';
            loadingStatus.innerText = error.message;
        }
    }

    async function performAutoHunt() {
        const query = productInput.value.trim();
        if (!query) {
            alert('Please enter a product name first!');
            return;
        }

        // UI State: Auto-Hunt mode
        resultsSection.style.display = 'block';
        resultsGrid.innerHTML = '';
        resultTitle.innerText = 'AUTO-HUNT ACTIVE';
        loadingStatus.innerText = 'SCANNING WEB $\rightarrow$ COMPARING PRICES $\rightarrow$ EXECUTING ADD-TO-CART...';

        autoHuntBtn.disabled = true;
        autoHuntBtn.innerText = "HUNTING...";

        try {
            const response = await fetch('/api/auto-hunt', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ q: query })
            });
            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            // Display the result as a single large "Winner" card
            const winnerCard = document.createElement('div');
            winnerCard.className = 'card';
            winnerCard.style.gridColumn = '1 / -1'; // span full width
            winnerCard.style.border = '2px solid var(--highlight)';
            winnerCard.style.textAlign = 'center';
            winnerCard.innerHTML = `
                <div style="font-family: var(--font-mono); color: var(--highlight); margin-bottom: 10px;">MISSION ACCOMPLISHED</div>
                <div style="font-size: 1.5rem; font-weight: 800; margin-bottom: 15px;">${data.message}</div>
                <div style="font-size: 0.9rem; color: var(--muted);">The lowest price was identified and added to your cart automatically.</div>
            `;
            resultsGrid.appendChild(winnerCard);

            loadingStatus.innerText = "MISSION COMPLETE";

        } catch (error) {
            console.error('Auto-Hunt Error:', error);
            resultTitle.innerText = 'AUTO-HUNT FAILED';
            loadingStatus.innerText = error.message;
        } finally {
            autoHuntBtn.disabled = false;
            autoHuntBtn.innerText = 'AUTO-HUNT';
        }
    }

    searchBtn.addEventListener('click', performSearch);
    autoHuntBtn.addEventListener('click', performAutoHunt);

    // Add event listeners to all Buy buttons
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('buy-btn')) {
            const btn = e.target;
            const url = btn.getAttribute('data-url');
            const originalText = btn.innerText;

            btn.innerText = "BOT WORKING...";
            btn.style.opacity = "0.5";
            btn.disabled = true;

            fetch('/api/add-to-cart', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: url })
            })
            .then(res => res.json())
            .then(result => {
                if (result.status === 'success') {
                    alert("🚀 Success! The agent has added the item to your cart.");
                } else {
                    alert("❌ Bot failed: " + (result.message || "Could not add to cart."));
                }
            })
            .catch(error => alert("Error: " + error.message))
            .finally(() => {
                btn.innerText = originalText;
                btn.style.opacity = "1";
                btn.disabled = false;
            });
        }
    });

    productInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') performSearch();
    });
});
