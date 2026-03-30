if (window.Telegram?.WebApp) {
    try {
        window.Telegram.WebApp.requestFullscreen();
    } catch (e) {
        window.Telegram.WebApp.expand();
    }
}

const params = new URLSearchParams(window.location.search);
const movieId = params.get("id");

// ─── HELPERS ───────────────────────────────────────────────
function formatLength(min) {
    if (!min) return null;
    const h = Math.floor(min / 60);
    const m = min % 60;
    return h > 0 ? `${h}ч ${m}мин` : `${m}мин`;
}

function getRatingColor(rating) {
    if (rating >= 7) return "rgba(232,201,122,0.4)";
    if (rating >= 5) return "rgba(150,150,150,0.3)";
    return "rgba(192,57,43,0.4)";
}

// ─── RENDER ────────────────────────────────────────────────
function renderMovie(movie) {
    // Poster
    const posterEl = document.getElementById("poster");
    posterEl.src = `/proxy/poster?url=${encodeURIComponent(movie.poster)}`;
    posterEl.onerror = () => { posterEl.src = movie.poster; };

    // Titles
    document.title = `${movie.name} — КиноЛинк`;
    document.getElementById("title").innerText = movie.name;

    if (movie.original_name && movie.original_name !== movie.name) {
        document.getElementById("originalTitle").innerText = movie.original_name;
    }

    // Kinopoisk rating
    if (movie.rating && movie.rating > 0) {
        document.getElementById("ratingNum").innerText = movie.rating.toFixed(1);
        document.getElementById("ratingBadge").style.borderColor = getRatingColor(movie.rating);
    }

    // IMDb rating
    if (movie.rating_imdb && movie.rating_imdb > 0) {
        document.getElementById("ratingImdbNum").innerText = movie.rating_imdb.toFixed(1);
    } else {
        document.getElementById("ratingImdb").style.display = "none";
    }

    // Meta pills: year, duration
    const metaItems = [
        movie.year        && { icon: "📅", text: movie.year },
        movie.film_length && { icon: "🕐", text: formatLength(movie.film_length) },
    ].filter(Boolean);

    document.getElementById("metaRow").innerHTML = metaItems
        .map(p => `<div class="meta-pill"><span class="icon">${p.icon}</span>${p.text}</div>`)
        .join("");

    // Genre tags
    document.getElementById("genres").innerHTML = (movie.genres || [])
        .map(g => `<span class="tag">${g}</span>`)
        .join("");

    // Country tags
    document.getElementById("countries").innerHTML = (movie.countries || [])
        .map(c => `<span class="tag country">${c}</span>`)
        .join("");

    // Description
    if (movie.description) {
        document.getElementById("description").innerText = movie.description;
    }

    // Player
    const playerDiv = document.getElementById("kinobd");
    playerDiv.setAttribute("data-kinopoisk", movie.id);

    const script = document.createElement("script");
    script.src = "https://kinobd.net/js/player_.js";
    document.body.appendChild(script);

    // Show content, hide skeleton
    document.getElementById("loadingState").classList.remove("active");
    document.getElementById("loadedState").classList.add("active");
}

// ─── LOAD ──────────────────────────────────────────────────
async function loadMovie() {
    if (!movieId) {
        showError();
        return;
    }

    try {
        const res = await fetch(`/movies/${movieId}`);
        if (!res.ok) throw new Error("not found");
        const movie = await res.json();
        renderMovie(movie);
    } catch (err) {
        showError();
    }
}

function showError() {
    document.getElementById("loadingState").classList.remove("active");
    document.getElementById("errorScreen").classList.add("active");
}

loadMovie();