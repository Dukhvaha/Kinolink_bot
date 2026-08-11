const Core = window.KinolinkRouletteCore;
const webApp = window.Telegram?.WebApp;

if (webApp) {
    webApp.ready();
    webApp.expand();
    webApp.setHeaderColor?.("#080810");
    webApp.setBackgroundColor?.("#080810");
    webApp.BackButton?.show();
    webApp.BackButton?.onClick(() => window.location.assign("/apps"));
}

const STORAGE_KEY = "kinolink:movieRoulette:v2";
const FILTERS = ["all", "movie", "tv", "anime"];
const DEMO_ENTRIES = [
    { key: "tt0816692", title: "Интерстеллар", listTitle: "Интерстеллар", imdbId: "tt0816692", year: 2014, mediaType: "movie", resolved: null },
    { key: "tt0903747", title: "Во все тяжкие", listTitle: "Во все тяжкие", imdbId: "tt0903747", year: 2008, mediaType: "tv", resolved: null },
    { key: "tt0245429", title: "Унесённые призраками", listTitle: "Унесённые призраками", imdbId: "tt0245429", year: 2001, mediaType: "movie", resolved: null },
];

const elements = {
    csvInput: document.querySelector("#csvInput"),
    importButton: document.querySelector("#importButton"),
    importStatus: document.querySelector("#importStatus"),
    demoButton: document.querySelector("#demoButton"),
    titleInput: document.querySelector("#titleInput"),
    refreshButton: document.querySelector("#refreshButton"),
    clearButton: document.querySelector("#clearButton"),
    filters: document.querySelector("#filters"),
    movieList: document.querySelector("#movieList"),
    totalBadge: document.querySelector("#totalBadge"),
    reel: document.querySelector("#reel"),
    spinButton: document.querySelector("#spinButton"),
    resultSection: document.querySelector("#resultSection"),
};

const state = {
    entries: [],
    filter: "all",
    spinning: false,
    requestId: 0,
    inputTimer: 0,
};

function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;",
    })[char]);
}

function saveState() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
        entries: state.entries,
        filter: state.filter,
    }));
}

function restoreState() {
    try {
        const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
        if (saved && Array.isArray(saved.entries)) state.entries = saved.entries;
        if (saved && FILTERS.includes(saved.filter)) state.filter = saved.filter;
    } catch {
        localStorage.removeItem(STORAGE_KEY);
    }
    syncTextarea();
    render();
    if (state.entries.some((entry) => !entry.resolved)) hydrateEntries();
}

function setStatus(message, kind = "neutral") {
    elements.importStatus.textContent = message;
    elements.importStatus.dataset.state = kind;
}

function syncTextarea() {
    elements.titleInput.value = state.entries.map((entry) => entry.listTitle || entry.title).join("\n");
}

function entryCategory(entry) {
    return Core.categoryFor(entry);
}

function filteredEntries() {
    if (state.filter === "all") return state.entries;
    return state.entries.filter((entry) => entryCategory(entry) === state.filter);
}

function resolvedData(entry) {
    return entry.resolved || {
        imdb_id: entry.imdbId || "",
        tmdb_id: null,
        media_type: entry.mediaType || "movie",
        title: entry.title,
        year: entry.year,
        poster: null,
        rating: entry.imdbRating || 0,
        overview: "Данные о тайтле обновляются.",
        genres: entry.genres ? entry.genres.split(",").map((value) => value.trim()) : [],
        is_anime: false,
    };
}

function typeLabel(entry) {
    const category = entryCategory(entry);
    if (category === "anime") return "Аниме";
    return category === "tv" ? "Сериал" : "Фильм";
}

function posterMarkup(entry, className = "") {
    const movie = resolvedData(entry);
    if (movie.poster) {
        return `<img class="${className}" src="${escapeHtml(movie.poster)}" alt="Постер: ${escapeHtml(movie.title)}" loading="lazy" referrerpolicy="no-referrer">`;
    }
    return `<div class="poster-placeholder ${className}">${escapeHtml(movie.title)}</div>`;
}

function renderCounts() {
    const counts = { all: state.entries.length, movie: 0, tv: 0, anime: 0 };
    state.entries.forEach((entry) => {
        const category = entryCategory(entry);
        if (Object.prototype.hasOwnProperty.call(counts, category)) counts[category] += 1;
    });

    elements.filters.querySelectorAll("[data-filter]").forEach((button) => {
        const filter = button.dataset.filter;
        const active = filter === state.filter;
        button.classList.toggle("is-active", active);
        button.setAttribute("aria-pressed", String(active));
        button.querySelector("span").textContent = String(counts[filter]);
    });

    const visible = filteredEntries().length;
    const total = state.entries.length;
    elements.totalBadge.textContent = state.filter === "all"
        ? `${total} ${Core.plural(total, "позиция", "позиции", "позиций")}`
        : `${visible} из ${total}`;
    elements.spinButton.disabled = state.spinning || visible === 0;
}

function renderMovieList() {
    const entries = filteredEntries();
    if (!entries.length) {
        elements.movieList.innerHTML = `<div class="list-empty">${state.entries.length ? "В этой категории пока нет позиций." : "Импортируй IMDb CSV или добавь названия вручную."}</div>`;
        return;
    }

    elements.movieList.innerHTML = entries.map((entry) => {
        const movie = resolvedData(entry);
        const details = [typeLabel(entry), movie.year, movie.imdb_id].filter(Boolean).join(" · ");
        return `
            <article class="list-item" data-key="${escapeHtml(entry.key)}">
                <div class="list-poster">${posterMarkup(entry)}</div>
                <div class="list-copy">
                    <strong>${escapeHtml(movie.title)}</strong>
                    <span>${escapeHtml(details)}</span>
                </div>
                <button class="remove-button" type="button" aria-label="Удалить ${escapeHtml(movie.title)}">×</button>
            </article>
        `;
    }).join("");
}

function renderReel() {
    const entries = filteredEntries();
    elements.reel.style.transition = "none";
    elements.reel.style.transform = "translateX(0)";
    if (!entries.length) {
        elements.reel.innerHTML = '<div class="reel-empty">Список для рулетки пока пуст</div>';
        return;
    }

    const repeated = Array.from({ length: 6 }, () => entries).flat();
    elements.reel.innerHTML = repeated.map((entry) => {
        const movie = resolvedData(entry);
        return `
            <article class="roulette-card">
                ${posterMarkup(entry)}
                <strong>${escapeHtml(movie.title)}</strong>
            </article>
        `;
    }).join("");
    requestAnimationFrame(() => { elements.reel.style.transition = ""; });
}

function render() {
    renderCounts();
    renderMovieList();
    renderReel();
}

function chunks(items, size) {
    const result = [];
    for (let index = 0; index < items.length; index += size) result.push(items.slice(index, index + size));
    return result;
}

async function hydrateEntries(force = false) {
    const requestId = ++state.requestId;
    const targets = state.entries.filter((entry) => force || !entry.resolved);
    if (!targets.length) {
        setStatus(state.entries.length ? "Список уже обновлён." : "Добавь позиции для обновления.", state.entries.length ? "success" : "neutral");
        return;
    }

    if (force) targets.forEach((entry) => { entry.resolved = null; });
    elements.importButton.disabled = true;
    setStatus(`Обновляю данные: 0 из ${targets.length}…`);
    let completed = 0;

    try {
        for (const group of chunks(targets, 40)) {
            const response = await fetch("/api/roulette/resolve", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    items: group.map((entry) => ({
                        imdb_id: entry.imdbId || null,
                        title: entry.title,
                        year: entry.year || null,
                        media_type: ["movie", "tv"].includes(entry.mediaType) ? entry.mediaType : null,
                    })),
                }),
            });
            if (!response.ok) throw new Error(`Kinolink API: ${response.status}`);
            const payload = await response.json();
            payload.items.forEach((item, index) => {
                if (group[index]) group[index].resolved = item.match || null;
            });
            completed += group.length;
            if (requestId !== state.requestId) return;
            saveState();
            render();
            setStatus(`Обновляю данные: ${completed} из ${targets.length}…`);
        }

        const matched = targets.filter((entry) => entry.resolved).length;
        setStatus(`Готово: найдено ${matched} из ${targets.length}.`, matched ? "success" : "error");
    } catch (error) {
        console.warn(error);
        setStatus("Не удалось обновить данные. Проверь backend Kinolink и повтори.", "error");
    } finally {
        elements.importButton.disabled = false;
        saveState();
        render();
    }
}

async function importCsv(file) {
    if (!file) return;
    if (file.size > 8 * 1024 * 1024) {
        setStatus("CSV слишком большой. Максимальный размер — 8 МБ.", "error");
        return;
    }

    try {
        const entries = Core.parseImdbWatchlist(await file.text());
        state.requestId += 1;
        state.entries = entries;
        state.filter = "all";
        syncTextarea();
        saveState();
        render();
        setStatus(`Импортировано ${entries.length} ${Core.plural(entries.length, "позиция", "позиции", "позиций")}.`);
        await hydrateEntries();
    } catch (error) {
        setStatus(error.message || "Не удалось прочитать IMDb CSV.", "error");
    } finally {
        elements.csvInput.value = "";
    }
}

function syncEntriesFromTextarea() {
    const existing = new Map(state.entries.map((entry) => [Core.titleKey(entry.listTitle || entry.title), entry]));
    const seen = new Set();
    const next = [];
    elements.titleInput.value.split(/\r?\n/).forEach((line) => {
        const title = Core.normalizeTitle(line);
        const key = Core.titleKey(title);
        if (!title || seen.has(key)) return;
        seen.add(key);
        next.push(existing.get(key) || {
            key: `manual:${key}`,
            title,
            listTitle: title,
            imdbId: "",
            year: null,
            mediaType: null,
            resolved: null,
        });
    });
    state.requestId += 1;
    state.entries = next;
    saveState();
    render();
    hydrateEntries();
}

function removeEntry(key) {
    state.requestId += 1;
    state.entries = state.entries.filter((entry) => entry.key !== key);
    syncTextarea();
    saveState();
    render();
}

function watchUrl(entry) {
    const movie = resolvedData(entry);
    if (!movie.tmdb_id || !movie.media_type) return "";
    const url = new URL("/", window.location.origin);
    url.searchParams.set("type", movie.media_type);
    url.searchParams.set("id", movie.tmdb_id);
    if (movie.imdb_id || entry.imdbId) url.searchParams.set("imdb_id", movie.imdb_id || entry.imdbId);
    url.searchParams.set("tmdb_id", movie.tmdb_id);
    url.searchParams.set("title", movie.title || entry.title);
    if (movie.year || entry.year) url.searchParams.set("year", movie.year || entry.year);
    url.searchParams.set("source", "movie_roulette");
    return url.toString();
}

function renderResult(entry) {
    const movie = resolvedData(entry);
    const url = watchUrl(entry);
    const meta = [typeLabel(entry), movie.year, movie.rating ? `★ ${movie.rating}` : "", movie.imdb_id || entry.imdbId]
        .filter(Boolean)
        .map((value) => `<span>${escapeHtml(value)}</span>`)
        .join("");

    elements.resultSection.innerHTML = `
        <article class="result-card">
            <div class="result-poster">${posterMarkup(entry)}</div>
            <div class="result-copy">
                <h2>${escapeHtml(movie.title)}</h2>
                <div class="result-meta">${meta}</div>
                <p>${escapeHtml(movie.overview || "Описание пока не найдено.")}</p>
                <button class="watch-button" type="button" data-watch-url="${escapeHtml(url)}" ${url ? "" : "disabled"}>Смотреть в KINOLINK</button>
            </div>
        </article>
    `;
}

function spin() {
    const entries = filteredEntries();
    if (state.spinning || !entries.length) return;

    const winnerIndex = Math.floor(Math.random() * entries.length);
    const targetIndex = entries.length * 4 + winnerIndex;
    const card = elements.reel.querySelector(".roulette-card");
    const reelWindow = document.querySelector(".reel-window");
    if (!card || !reelWindow) return;

    const gap = Number.parseFloat(getComputedStyle(elements.reel).columnGap) || 0;
    const step = card.getBoundingClientRect().width + gap;
    const offset = targetIndex * step - reelWindow.clientWidth / 2 + card.getBoundingClientRect().width / 2 + 18;

    state.spinning = true;
    renderCounts();
    elements.reel.style.transition = "none";
    elements.reel.style.transform = "translateX(0)";
    requestAnimationFrame(() => requestAnimationFrame(() => {
        elements.reel.style.transition = "transform 4.8s cubic-bezier(0.12, 0.72, 0.12, 1)";
        elements.reel.style.transform = `translateX(-${offset}px)`;
    }));

    window.setTimeout(() => {
        state.spinning = false;
        renderCounts();
        renderResult(entries[winnerIndex]);
        elements.resultSection.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }, 4900);
}

elements.importButton.addEventListener("click", () => elements.csvInput.click());
elements.csvInput.addEventListener("change", () => importCsv(elements.csvInput.files?.[0]));
elements.demoButton.addEventListener("click", () => {
    state.requestId += 1;
    state.entries = DEMO_ENTRIES.map((entry) => ({ ...entry }));
    state.filter = "all";
    syncTextarea();
    saveState();
    render();
    hydrateEntries();
});
elements.refreshButton.addEventListener("click", () => hydrateEntries(true));
elements.clearButton.addEventListener("click", () => {
    state.requestId += 1;
    state.entries = [];
    state.filter = "all";
    syncTextarea();
    saveState();
    setStatus("Список очищен.");
    render();
});
elements.titleInput.addEventListener("input", () => {
    window.clearTimeout(state.inputTimer);
    state.inputTimer = window.setTimeout(syncEntriesFromTextarea, 650);
});
elements.filters.addEventListener("click", (event) => {
    const button = event.target.closest("[data-filter]");
    if (!button || !FILTERS.includes(button.dataset.filter)) return;
    state.filter = button.dataset.filter;
    saveState();
    render();
});
elements.movieList.addEventListener("click", (event) => {
    const button = event.target.closest(".remove-button");
    if (button) removeEntry(button.closest(".list-item").dataset.key);
});
elements.resultSection.addEventListener("click", (event) => {
    const button = event.target.closest("[data-watch-url]");
    if (button && button.dataset.watchUrl) window.location.assign(button.dataset.watchUrl);
});
elements.spinButton.addEventListener("click", spin);

restoreState();
