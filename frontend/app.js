if (window.Telegram?.WebApp) {
    try {
        window.Telegram.WebApp.requestFullscreen();
    } catch (e) {
        window.Telegram.WebApp.expand();
    }
}

const params = new URLSearchParams(window.location.search);
const movieId = params.get("id");
const PUBLISHER_ID = "678153547";
const RENDEX_SDK_URL = "https://graphicslab.io/sdk/v2/rendex-sdk.min.js";

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

function appendTextTag(container, text, className = "tag") {
    const tag = document.createElement("span");
    tag.className = className;
    tag.textContent = text;
    container.appendChild(tag);
}

function loadRendexSdk() {
    const oldScript = document.getElementById("rendexSdk");
    if (oldScript) oldScript.remove();

    const script = document.createElement("script");
    script.id = "rendexSdk";
    script.src = `${RENDEX_SDK_URL}?v=${Date.now()}`;
    document.body.appendChild(script);
}

function renderPlayer(kpId) {
    const playerWrap = document.getElementById("rendexPlayer");
    playerWrap.innerHTML = "";

    const player = document.createElement("ins");
    player.setAttribute("data-publisher-id", PUBLISHER_ID);
    player.setAttribute("data-type", "kp");
    player.setAttribute("data-id", kpId);
    player.setAttribute("data-design", "2");
    player.setAttribute("data-poster", "true");
    player.setAttribute("data-width", "100%");
    player.setAttribute("data-height", "450px");

    playerWrap.appendChild(player);
    loadRendexSdk();
}

// ─── RENDER ────────────────────────────────────────────────
function renderMovie(movie) {
    // Poster
    const posterEl = document.getElementById("poster");
    if (movie.poster) {
        posterEl.src = `/proxy/poster?url=${encodeURIComponent(movie.poster)}`;
        posterEl.onerror = () => { posterEl.src = movie.poster; };
    }

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

    const metaRow = document.getElementById("metaRow");
    metaRow.innerHTML = "";
    metaItems.forEach((item) => {
        const pill = document.createElement("div");
        const icon = document.createElement("span");

        pill.className = "meta-pill";
        icon.className = "icon";
        icon.textContent = item.icon;
        pill.append(icon, document.createTextNode(String(item.text)));
        metaRow.appendChild(pill);
    });

    // Genre tags
    const genres = document.getElementById("genres");
    genres.innerHTML = "";
    (movie.genres || []).forEach((genre) => appendTextTag(genres, genre));

    // Country tags
    const countries = document.getElementById("countries");
    countries.innerHTML = "";
    (movie.countries || []).forEach((country) => appendTextTag(countries, country, "tag country"));

    // Description
    if (movie.description) {
        document.getElementById("description").innerText = movie.description;
    }

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

    renderPlayer(movieId);

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
