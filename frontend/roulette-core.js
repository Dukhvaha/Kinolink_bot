(function exposeRouletteCore(root, factory) {
    const api = factory();
    if (typeof module !== "undefined" && module.exports) module.exports = api;
    root.KinolinkRouletteCore = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function createRouletteCore() {
    function normalizeTitle(value) {
        return String(value || "").trim().replace(/\s+/g, " ");
    }

    function normalizeHeader(value) {
        return String(value || "")
            .replace(/^\uFEFF/, "")
            .trim()
            .toLowerCase()
            .replace(/[^a-z0-9а-яё]+/gi, "");
    }

    function titleKey(value) {
        return normalizeTitle(value).toLowerCase().replace(/ё/g, "е");
    }

    function parseCsv(text) {
        const rows = [];
        let row = [];
        let value = "";
        let quoted = false;

        for (let index = 0; index < text.length; index += 1) {
            const char = text[index];
            const next = text[index + 1];

            if (char === '"' && quoted && next === '"') {
                value += '"';
                index += 1;
            } else if (char === '"') {
                quoted = !quoted;
            } else if (char === "," && !quoted) {
                row.push(value);
                value = "";
            } else if ((char === "\n" || char === "\r") && !quoted) {
                if (char === "\r" && next === "\n") index += 1;
                row.push(value);
                if (row.some((cell) => cell.trim())) rows.push(row);
                row = [];
                value = "";
            } else {
                value += char;
            }
        }

        row.push(value);
        if (row.some((cell) => cell.trim())) rows.push(row);
        return rows;
    }

    function classifyMediaType(value) {
        const normalized = String(value || "").toLowerCase();
        if (/tv movie|tv special|tv short/.test(normalized)) return "movie";
        if (/series|episode|mini|television|tv/.test(normalized)) return "tv";
        if (/game|podcast/.test(normalized)) return "other";
        return "movie";
    }

    function parseImdbWatchlist(text) {
        const rows = parseCsv(text);
        if (rows.length < 2) throw new Error("В CSV нет позиций для импорта.");

        const headers = rows[0].map(normalizeHeader);
        const indexes = new Map(headers.map((header, index) => [header, index]));
        const read = (row, aliases) => {
            const header = aliases.map(normalizeHeader).find((alias) => indexes.has(alias));
            return header ? String(row[indexes.get(header)] || "").trim() : "";
        };

        if (!["title", "originaltitle"].some((header) => indexes.has(header))) {
            throw new Error("Не найден столбец Title. Нужен CSV из IMDb Watchlist.");
        }

        const entries = [];
        const seen = new Set();

        rows.slice(1).forEach((row) => {
            const title = normalizeTitle(read(row, ["Title", "Original Title"]));
            if (!title) return;

            const rawType = read(row, ["Title Type", "Type"]);
            const mediaType = classifyMediaType(rawType);
            if (mediaType === "other") return;

            const rawId = read(row, ["Const", "IMDb ID", "tconst"]);
            const rawUrl = read(row, ["URL", "IMDb URL"]);
            const imdbId = (rawId.match(/tt\d+/i) || rawUrl.match(/tt\d+/i) || [""])[0].toLowerCase();
            const yearMatch = read(row, ["Year", "Release Year"]).match(/\d{4}/);
            const year = yearMatch ? Number(yearMatch[0]) : null;
            const key = imdbId || `${titleKey(title)}:${year || ""}`;
            if (seen.has(key)) return;
            seen.add(key);

            entries.push({
                key,
                title,
                listTitle: title,
                imdbId,
                year,
                mediaType,
                imdbRating: read(row, ["IMDb Rating", "Rating"]),
                genres: read(row, ["Genres", "Genre"]),
                resolved: null,
            });
        });

        if (!entries.length) throw new Error("В CSV не найдено фильмов или сериалов.");

        const counts = new Map();
        entries.forEach((entry) => counts.set(titleKey(entry.title), (counts.get(titleKey(entry.title)) || 0) + 1));
        const usedLabels = new Set();
        entries.forEach((entry) => {
            let label = entry.title;
            if (counts.get(titleKey(entry.title)) > 1) label = `${entry.title} (${entry.year || entry.imdbId || "IMDb"})`;
            if (usedLabels.has(titleKey(label))) label = `${label} · ${entry.imdbId || "другая версия"}`;
            entry.listTitle = label;
            usedLabels.add(titleKey(label));
        });

        return entries;
    }

    function categoryFor(entry) {
        if (entry.resolved && entry.resolved.is_anime) return "anime";
        if (entry.resolved && entry.resolved.media_type) return entry.resolved.media_type;
        return entry.mediaType || "movie";
    }

    function plural(number, one, few, many) {
        const mod10 = number % 10;
        const mod100 = number % 100;
        if (mod10 === 1 && mod100 !== 11) return one;
        if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return few;
        return many;
    }

    return {
        categoryFor,
        normalizeTitle,
        parseCsv,
        parseImdbWatchlist,
        plural,
        titleKey,
    };
});
