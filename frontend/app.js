const params = new URLSearchParams(window.location.search);
const movieId = params.get("id");

async function loadMovie() {
    try {
        const res = await fetch(`http://localhost:8000/movie/${movieId}`);
        const movie = await res.json();

        renderMovie(movie);

    } catch (err) {
        console.error(err);
        document.body.innerHTML = "<h1>Ошибка загрузки</h1>";
    }
}

function renderMovie(movie) {
    document.getElementById("poster").src = movie.poster;
    document.getElementById("title").innerText = movie.name;

    document.getElementById("meta").innerText =
        `${movie.year} • ⭐ ${movie.rating}`;

    document.getElementById("description").innerText =
        movie.description || "Описание отсутствует";

    const genresDiv = document.getElementById("genres");
    genresDiv.innerHTML = "";

    movie.genres.forEach(g => {
        const span = document.createElement("span");
        span.className = "genre";
        span.innerText = g;
        genresDiv.appendChild(span);
    });

    // ПЛЕЕР
    const playerDiv = document.getElementById("kinobd");
    playerDiv.setAttribute("data-kinopoisk", movie.id);

    const script = document.createElement("script");
    script.src = "https://kinobd.net/js/player_.js";
    document.body.appendChild(script);
}

loadMovie();

console.log("movieId:", movieId);
console.log("movie:", movie);
console.log("MOVIE:", movie);
