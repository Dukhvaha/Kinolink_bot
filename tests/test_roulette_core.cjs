const test = require("node:test");
const assert = require("node:assert/strict");

const Core = require("../frontend/roulette-core.js");

test("IMDb CSV keeps a title with commas as one position", () => {
    const csv = [
        "Position,Const,Title,URL,Title Type,IMDb Rating,Year,Genres",
        '1,tt1234567,"Once Upon a Time in America, Part II",https://www.imdb.com/title/tt1234567/,Movie,8.1,2025,"Drama, Crime"',
    ].join("\n");

    const entries = Core.parseImdbWatchlist(csv);

    assert.equal(entries.length, 1);
    assert.equal(entries[0].title, "Once Upon a Time in America, Part II");
    assert.equal(entries[0].imdbId, "tt1234567");
    assert.equal(entries[0].genres, "Drama, Crime");
});

test("anime belongs only to the anime filter", () => {
    const entry = {
        mediaType: "movie",
        resolved: { media_type: "movie", is_anime: true },
    };

    assert.equal(Core.categoryFor(entry), "anime");
    assert.notEqual(Core.categoryFor(entry), "movie");
    assert.notEqual(Core.categoryFor(entry), "tv");
});

test("IMDb id can be read from URL when Const is empty", () => {
    const csv = [
        "Const,Title,URL,Title Type,Year",
        ",Dark,https://www.imdb.com/title/tt5753856/,TV Series,2017",
    ].join("\n");

    const [entry] = Core.parseImdbWatchlist(csv);

    assert.equal(entry.imdbId, "tt5753856");
    assert.equal(entry.mediaType, "tv");
});
