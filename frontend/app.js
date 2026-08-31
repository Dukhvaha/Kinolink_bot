const telegramWebApp = window.Telegram?.WebApp;

if (telegramWebApp) {
    telegramWebApp.ready();
    telegramWebApp.expand();

    try {
        telegramWebApp.requestFullscreen();
    } catch (e) {
        // Fullscreen is not available in every Telegram client.
    }
}

const params = new URLSearchParams(window.location.search);
const movieId = params.get("id");
const mediaType = params.get("type") || "movie";
const PUBLISHER_ID = "678153547";
const RENDEX_SDK_URL = "https://graphicslab.io/sdk/v2/rendex-sdk.min.js";
const PLAYER_LOAD_TIMEOUT_MS = 10000;
let rendexSdkPromise = null;

function trackView() {
    const user = telegramWebApp?.initDataUnsafe?.user;
    const payload = {
        event_type: telegramWebApp ? "mini_app_open" : "site_open",
        media_type: mediaType,
        movie_id: movieId ? Number(movieId) : null,
        user_id: user?.id || null,
        username: user?.username || null,
        first_name: user?.first_name || null,
    };

    const body = JSON.stringify(payload);

    if (navigator.sendBeacon) {
        const blob = new Blob([body], { type: "application/json" });
        navigator.sendBeacon("/track-view", blob);
        return;
    }

    fetch("/track-view", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body,
        keepalive: true,
    }).catch(() => {});
}

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
    if (rendexSdkPromise) return rendexSdkPromise;

    rendexSdkPromise = new Promise((resolve, reject) => {
        const existingScript = document.getElementById("rendexSdk");
        if (existingScript?.dataset.loaded === "true") {
            resolve();
            return;
        }

        const script = existingScript || document.createElement("script");
        const timeoutId = window.setTimeout(() => {
            reject(new Error("Rendex SDK loading timed out"));
        }, PLAYER_LOAD_TIMEOUT_MS);

        script.id = "rendexSdk";
        script.src = RENDEX_SDK_URL;
        script.async = true;
        script.onload = () => {
            window.clearTimeout(timeoutId);
            script.dataset.loaded = "true";
            resolve();
        };
        script.onerror = () => {
            window.clearTimeout(timeoutId);
            reject(new Error("Rendex SDK failed to load"));
        };

        if (!existingScript) document.body.appendChild(script);
    });

    return rendexSdkPromise;
}

function showPlayerMessage(playerWrap, message, className = "player-empty") {
    playerWrap.innerHTML = "";
    const status = document.createElement("div");
    status.className = className;
    status.textContent = message;
    playerWrap.appendChild(status);
}

function waitForPlayerFrame(playerWrap, player, timeoutMs) {
    return new Promise((resolve, reject) => {
        const isReady = () => Boolean(
            playerWrap.querySelector("iframe, video") || player.children.length
        );

        if (isReady()) {
            resolve();
            return;
        }

        const observer = new MutationObserver(() => {
            if (!isReady()) return;
            observer.disconnect();
            window.clearTimeout(timeoutId);
            resolve();
        });
        const timeoutId = window.setTimeout(() => {
            observer.disconnect();
            reject(new Error("Player frame loading timed out"));
        }, timeoutMs);

        observer.observe(playerWrap, { childList: true, subtree: true });
    });
}

async function mountPlayer(playerWrap, playerType, playerId) {
    const startedAt = Date.now();
    playerWrap.innerHTML = "";

    const loading = document.createElement("div");
    loading.className = "player-loading";
    loading.textContent = "Загружаем плеер...";
    playerWrap.appendChild(loading);

    const player = document.createElement("ins");
    player.setAttribute("data-publisher-id", PUBLISHER_ID);
    player.setAttribute("data-type", playerType || "imdb");
    player.setAttribute("data-id", playerId);
    player.setAttribute("data-design", "2");
    player.setAttribute("data-poster", "true");
    player.setAttribute("data-nopreload", "true");
    player.setAttribute("data-width", "100%");
    player.setAttribute("data-height", "450px");
    playerWrap.appendChild(player);

    try {
        await loadRendexSdk();
        const remainingTime = Math.max(
            1,
            PLAYER_LOAD_TIMEOUT_MS - (Date.now() - startedAt),
        );
        await waitForPlayerFrame(playerWrap, player, remainingTime);
        loading.remove();
    } catch (error) {
        showPlayerMessage(
            playerWrap,
            "Плеер не удалось загрузить. Скорее всего, ошибка возникла из-за включённого VPN. Попробуйте сменить VPN-сервер или временно отключить VPN и обновить страницу.",
            "player-empty player-error",
        );
    }
}

function renderPlayer(playerType, playerId) {
    const playerWrap = document.getElementById("rendexPlayer");

    if (!playerId) {
        showPlayerMessage(playerWrap, "Плеер для этого фильма пока недоступен.");
        return;
    }

    showPlayerMessage(
        playerWrap,
        "Плеер загрузится, когда ты прокрутишь страницу к нему.",
        "player-placeholder",
    );

    const startLoading = () => mountPlayer(playerWrap, playerType, playerId);
    if (!("IntersectionObserver" in window)) {
        startLoading();
        return;
    }

    const observer = new IntersectionObserver((entries) => {
        if (!entries.some((entry) => entry.isIntersecting)) return;
        observer.disconnect();
        startLoading();
    }, { rootMargin: "320px 0px" });

    observer.observe(playerWrap);
}

// ─── RENDER ────────────────────────────────────────────────
function renderMovie(movie) {
    // Poster
    const posterEl = document.getElementById("poster");
    if (movie.poster) {
        posterEl.src = movie.poster;
    }

    // Titles
    document.title = `${movie.name} — КиноЛинк`;
    document.getElementById("title").innerText = movie.name;

    if (movie.original_name && movie.original_name !== movie.name) {
        document.getElementById("originalTitle").innerText = movie.original_name;
    }

    // Primary rating
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

    renderPlayer(movie.player_type, movie.player_id);

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
        const res = await fetch(`/movies/${mediaType}/${movieId}`);
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

trackView();
loadMovie();
