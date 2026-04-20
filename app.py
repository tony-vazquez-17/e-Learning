from flask import Flask, render_template, abort, make_response # type: ignore
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import json

app = Flask(__name__, static_folder="static", template_folder="templates")


def get_youtube_embed_url(video_identifier):
    if not isinstance(video_identifier, str):
        return ""

    video_identifier = video_identifier.strip()
    if not video_identifier:
        return ""

    if video_identifier.startswith("http"):
        parsed = urlparse(video_identifier)
        hostname = parsed.hostname or ""
        path = parsed.path or ""

        if hostname.endswith("youtu.be"):
            video_id = path.lstrip("/")
            return f"https://www.youtube.com/embed/{video_id}"

        if hostname.endswith("youtube.com") or hostname.endswith("www.youtube.com"):
            if path.startswith("/watch"):
                query = parse_qs(parsed.query)
                video_id = query.get("v", [""])[0]
                return f"https://www.youtube.com/embed/{video_id}" if video_id else video_identifier
            if path.startswith("/embed/"):
                return video_identifier
            if path.startswith("/shorts/"):
                video_id = path.split("/")[-1]
                return f"https://www.youtube.com/embed/{video_id}"

        return video_identifier

    return f"https://www.youtube.com/embed/{video_identifier}"

DATA_PATH = Path(__file__).resolve().parent / "data.json"
with DATA_PATH.open("r", encoding="utf-8") as json_file:
    DATA = json.load(json_file)

GRADOS = DATA["grados"]
TEMAS = DATA["temas"]


@app.route("/")
def index():
    grados = list(GRADOS.keys())
    return render_template("index.html", grados=grados)


@app.route("/grado/<grado>")
def grado(grado):
    if grado not in GRADOS:
        abort(404)
    materias = GRADOS[grado]
    return render_template("grado.html", grado=grado, materias=materias)


@app.route("/materia/<grado>/<materia>")
def materia(grado, materia):
    if grado not in GRADOS or materia not in GRADOS[grado]:
        abort(404)
    
    temas = TEMAS.get(materia, [])
    return render_template("materia.html", grado=grado, materia=materia, temas=temas)


@app.route("/tema/<grado>/<materia>/<tema_id>")
def tema(grado, materia, tema_id):
    if grado not in GRADOS or materia not in GRADOS[grado]:
        abort(404)
    
    temas = TEMAS.get(materia, [])
    tema_data = next((t for t in temas if t["id"] == tema_id), None)
    
    if not tema_data:
        abort(404)
    
    video_url = get_youtube_embed_url(tema_data.get("videoYouTubeId", ""))
    return render_template(
        "tema.html",
        grado=grado,
        materia=materia,
        tema=tema_data,
        video_url=video_url
    )


@app.route("/download/<grado>")
def download_programa(grado):
    if grado not in GRADOS:
        abort(404)

    contenido = f"Programa de estudios para {grado}\n\n"
    for materia in GRADOS[grado]:
        contenido += f"- {materia}\n"

    buffer = BytesIO(contenido.encode("utf-8"))
    response = make_response(buffer.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename={grado}_programa.txt"
    response.headers["Content-Type"] = "text/plain; charset=utf-8"
    return response

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
