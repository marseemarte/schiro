from flask import Flask, render_template, request, redirect, url_for
import google.generativeai as genai

# Configurar la API de Gemini (poner tu API key)
genai.configure(api_key="AIzaSyAwrl33_B2bjbggoB-DwOmcZ2YJcXlfamg")

app = Flask(__name__)

# Prompt base (rol de la IA) con el orden solicitado
PROMPT_BASE = """
Sos un profesor paciente y divertido para chicos de primaria (7 a 12 años).
Respondé SIEMPRE en español y seguí este formato exactamente, con títulos y listas:

1) Explicación más técnica (nivel primario):
- Explicá el concepto con términos correctos pero accesibles.
- Usá 3 a 5 puntos claros.

2) Explicación simple:
- Reexplicá como si se lo contaras a un amigo de la misma edad.
- Frases cortas y ejemplos sencillos.

3) Ejemplos cotidianos dinámicos:
- 2 a 3 situaciones de la vida real, variadas, con pasos.
- Incluí números o elementos concretos cuando sirva.

4) Desafío para practicar (dinámico y divertido):
- Planteá una mini-actividad interactiva o juego breve (no solo un multiple choice).
- Invitá a que escriban/armen/experimenten algo (ej.: crea, dibuja, cuenta, mide, clasifica, arma un cuadro, etc.).
"""

@app.route("/", methods=["GET"]) 
def home():
    return render_template("index.html")


@app.route("/buscar", methods=["POST"]) 
def buscar():
    duda = request.form.get("duda", "").strip()
    if not duda:
        return redirect(url_for('home'))

    full_prompt = PROMPT_BASE + "\n\nDuda del alumno: " + duda
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(full_prompt)
    respuesta = getattr(response, 'text', '')

    # Render en plantilla de respuesta
    return render_template("respuesta.html", duda=duda, respuesta=respuesta)

if __name__ == "__main__":
    app.run(debug=True)
