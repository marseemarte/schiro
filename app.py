import json
import re
import os
from dotenv import load_dotenv

from flask import Flask, render_template, request, redirect, url_for
import google.generativeai as genai

# Cargar variables de entorno
load_dotenv()

# Configurar la API de Gemini
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY no está configurada. Por favor, crea un archivo .env con tu API key.")
genai.configure(api_key=api_key)

app = Flask(__name__)

# Prompt base (rol de la IA) con el orden solicitado
PROMPT_BASE = """
Sos un profesor paciente, divertido y claro que enseña a chicos de primaria (de 7 a 12 años).
Tu tarea es explicar temas escolares de forma ordenada, visual y entretenida.

IMPORTANTE:

Usá etiquetas HTML para estructurar la respuesta.

No uses asteriscos, guiones ni markdown.

Escribí SIEMPRE en español.

Al menos UNA VEZ por respuesta, incluí un emoji relacionado con la enseñanza o el tema y color distinto en palabras clave.

Separá las secciones con títulos (<h3>) y listas o párrafos (<ul>, <li>, <p>).

Evitá texto plano largo y sin formato.
Estructura obligatoria de cada respuesta:
<h3>1) Respuesta para la carpeta:</h3>
<ul>
  <li>Explicación técnica breve (3 a 5 puntos claros).</li>
  <li>Usá vocabulario correcto pero comprensible.</li>
</ul>

<h3>2) Explicación simple:</h3>
<p>Reexplicá el concepto con palabras simples, como si se lo contaras a un amigo.  
Frases cortas y fáciles de entender.</p>

<h3>3) Ejemplos cotidianos dinámicos:</h3>
<ul>
  <li>Ejemplo 1 con una situación real o cercana.</li>
  <li>Ejemplo 2 con otro contexto o acción concreta.</li>
  <li>Si querés, agregá un tercer ejemplo corto.</li>
</ul>

<h3>4) Desafío para practicar (divertido y creativo):</h3>
<p>Proponé una mini actividad práctica o juego breve.  
Debe invitar a escribir, dibujar, crear o experimentar.  
No hagas preguntas de opción múltiple.</p>

Ejemplo de cómo debería verse una respuesta generada:

<h3>1) Respuesta para la carpeta:</h3>
<ul>
  <li>La fotosíntesis es el proceso por el cual las plantas producen su alimento.</li>
  <li>Utilizan la luz del sol, el agua y el dióxido de carbono del aire.</li>
  <li>Este proceso ocurre en las hojas, dentro de los cloroplastos.</li>
  <li>Durante la fotosíntesis, se libera oxígeno al ambiente.</li>
</ul>

<h3>2) Explicación simple:</h3>
<p>Las plantas usan la luz del sol para preparar su comida, igual que si cocinaran su almuerzo.  
Con eso crecen fuertes y nos dan el aire que respiramos.</p>

<h3>3) Ejemplos cotidianos dinámicos:</h3>
<ul>
  <li>Cuando regás una planta y la ponés al sol, empieza a “trabajar” haciendo fotosíntesis.</li>
  <li>Si la dejás sin agua o sin luz, se pone triste y se marchita.</li>
  <li>Una planta junto a la ventana crece más rápido que una en la sombra.</li>
</ul>

<h3>4) Desafío para practicar (divertido y creativo):</h3>
<p>Colocá dos plantas: una al sol y otra en la sombra.  
Durante una semana, observá cuál crece más rápido y anotá tus resultados.  
Podés dibujar los cambios que veas cada día.</p>

"""

TEST_PROMPT_TEMPLATE = """
Sos un profesor creativo que diseña preguntas de opción múltiple para chicos y chicas de primaria (entre 8 y 12 años).
Creá 10 preguntas súper claras sobre el tema "{subject}".
Nivel solicitado: {level_text}

Las instrucciones obligatorias son:
- Escribí todo en ESPAÑOL neutro.
- Los enunciados deben ser breves, amigables y situados en situaciones cotidianas infantiles.
- Las opciones deben ser cortas (máx. 8 palabras) y diferentes entre sí.
- Añadí una pista/mnemotecnia divertida ("tip") para que el alumno recuerde la idea.
- Usá contenidos apropiados para primaria.

Respondé ÚNICAMENTE con un JSON válido siguiendo esta estructura exacta (sin texto adicional, ni explicaciones, ni bloques Markdown):
{{
  "subject": "{subject}",
  "questions": [
    {{
      "question": "Enunciado breve",
      "options": ["Opción A", "Opción B", "Opción C", "Opción D"],
      "correct": "Texto idéntico a la opción correcta",
      "tip": "Consejo o truco corto"
    }}
  ]
}}

Recordá devolver exactamente 10 preguntas.
"""

DIFFICULTIES = {
    "facil": "Nivel fácil",
    "intermedio": "Nivel intermedio",
    "desafiante": "Nivel desafiante",
}

DIFFICULTY_DESCRIPTIONS = {
    "facil": "Preguntas muy simples, con números pequeños y vocabulario cotidiano.",
    "intermedio": "Preguntas con un poco más de razonamiento y situaciones escolares.",
    "desafiante": "Preguntas que requieren pensar dos pasos y conectar ideas, siempre aptas para primaria.",
}


FALLBACK_TESTS = {
    "Matemática": {
        "facil": [
            {"question": "¿Cuánto es 5 + 7?", "options": ["10", "11", "12", "13"], "correct": "12", "tip": "Sumá primero 5 + 5 y agregá 2."},
            {"question": "Si tenés 9 caramelos y regalás 3, ¿cuántos quedan?", "options": ["3", "5", "6", "7"], "correct": "6", "tip": "Restá lo que regalaste."},
            {"question": "¿Qué número es el doble de 4?", "options": ["6", "8", "10", "12"], "correct": "8", "tip": "Duplicar es sumar el mismo número."},
            {"question": "Un paquete tiene 10 figuritas. Si comprás 2 paquetes, ¿cuántas figuritas tenés?", "options": ["10", "15", "20", "25"], "correct": "20", "tip": "Sumá 10 dos veces."},
            {"question": "¿Qué número es mayor?", "options": ["23", "32", "19", "13"], "correct": "32", "tip": "Miramos primero las decenas."},
            {"question": "Si una torta se corta en 4 partes iguales y comés 1, ¿qué fracción comiste?", "options": ["1/2", "1/3", "1/4", "2/4"], "correct": "1/4", "tip": "El denominador indica el total de partes."},
            {"question": "¿Cuánto falta para llegar de 18 a 20?", "options": ["1", "2", "3", "4"], "correct": "2", "tip": "Contá cuántos saltos necesitás."},
            {"question": "¿Cuál es la mitad de 12?", "options": ["4", "5", "6", "8"], "correct": "6", "tip": "Partí 12 en dos grupos iguales."},
            {"question": "Si una caja trae 3 lápices y tenés 4 cajas, ¿cuántos lápices hay?", "options": ["7", "9", "10", "12"], "correct": "12", "tip": "Multiplicá 3 x 4."},
            {"question": "¿Cuál es el resultado de 15 - 9?", "options": ["4", "5", "6", "7"], "correct": "6", "tip": "Restá primero 10 - 9 y luego sumá 5."}
        ],
        "intermedio": [
            {"question": "¿Cuánto es 36 + 47?", "options": ["63", "73", "83", "93"], "correct": "83", "tip": "Sumá decenas (30 + 40) y luego unidades."},
            {"question": "Si tenés 5 paquetes con 4 figuritas cada uno, ¿cuántas figuritas son?", "options": ["9", "16", "20", "25"], "correct": "20", "tip": "Multiplicá 5 x 4 para saber el total."},
            {"question": "¿Cuál es el doble de 28?", "options": ["46", "54", "56", "58"], "correct": "56", "tip": "Duplicar es sumar el mismo número dos veces."},
            {"question": "Una soga mide 1 metro. ¿Cuántos centímetros son?", "options": ["10 cm", "100 cm", "1000 cm", "10000 cm"], "correct": "100 cm", "tip": "1 metro equivale a 100 centímetros."},
            {"question": "¿Qué número es mayor?", "options": ["0,45", "0,54", "0,405", "0,504"], "correct": "0,54", "tip": "Compará decenas, luego centésimas."},
            {"question": "Si un triángulo tiene lados 3 cm, 4 cm y 5 cm, su perímetro es…", "options": ["7 cm", "9 cm", "10 cm", "12 cm"], "correct": "12 cm", "tip": "Sumá los tres lados para el perímetro."},
            {"question": "¿Cuánto falta para llegar de 67 a 100?", "options": ["23", "33", "43", "53"], "correct": "33", "tip": "100 - 67 te da la diferencia."},
            {"question": "Si una pizza se divide en 8 partes iguales y comés 3, ¿qué fracción comiste?", "options": ["3/5", "3/8", "5/8", "8/3"], "correct": "3/8", "tip": "El denominador es la cantidad total de partes."},
            {"question": "¿Qué operación resuelve 6 x 7?", "options": ["42", "36", "28", "56"], "correct": "42", "tip": "Recordá la tabla del 7."},
            {"question": "Si un número multiplicado por 10 es 470, ¿cuál era el número inicial?", "options": ["4,7", "47", "4700", "470"], "correct": "47", "tip": "Dividir por 10 corre la coma un lugar."}
        ],
        "desafiante": [
            {"question": "¿Cuál es el resultado de 125 + 98?", "options": ["203", "213", "223", "233"], "correct": "223", "tip": "Sumá primero 100 + 90 y luego las unidades."},
            {"question": "Si un rectángulo mide 6 cm por 9 cm, ¿cuál es su área?", "options": ["15 cm²", "45 cm²", "54 cm²", "60 cm²"], "correct": "54 cm²", "tip": "Área = base x altura."},
            {"question": "Tenés 3/4 de litro de jugo y tomás 1/8. ¿Cuánto queda?", "options": ["5/8", "2/3", "1/2", "3/8"], "correct": "5/8", "tip": "Buscá fracciones con el mismo denominador."},
            {"question": "¿Cuál es el promedio de 12, 14 y 16?", "options": ["12", "13", "14", "15"], "correct": "14", "tip": "Sumá todo y dividí por la cantidad de números."},
            {"question": "Si una bici recorre 5 km en 10 min, ¿cuántos km hace en una hora manteniendo la velocidad?", "options": ["10 km", "20 km", "25 km", "30 km"], "correct": "30 km", "tip": "Una hora tiene 60 min, es decir seis veces más."},
            {"question": "¿Qué número multiplicado por 9 da 324?", "options": ["18", "32", "34", "36"], "correct": "36", "tip": "Dividí 324 por 9."},
            {"question": "Si un tanque se llena 1/3 por la mañana y 2/5 por la tarde, ¿cuánto se llenó en total?", "options": ["13/15", "7/15", "11/15", "1"], "correct": "11/15", "tip": "Usá denominador común 15."},
            {"question": "Convertí 2,5 metros a centímetros.", "options": ["25 cm", "105 cm", "205 cm", "250 cm"], "correct": "250 cm", "tip": "Multiplicá metros x 100."},
            {"question": "Si la base de un triángulo es 12 cm y su altura 7 cm, ¿cuál es el área?", "options": ["42 cm²", "68 cm²", "72 cm²", "84 cm²"], "correct": "42 cm²", "tip": "Área = (base x altura) / 2."},
            {"question": "Un número es 8 más que otro. Si suman 46, ¿cuáles son?", "options": ["18 y 28", "19 y 27", "20 y 26", "21 y 25"], "correct": "19 y 27", "tip": "Restá 8 y dividí el resto en dos partes."}
        ]
    },
    "PDL": {
        "facil": [
            {"question": "¿Qué texto cuenta una historia corta?", "options": ["Receta", "Cuento", "Nota", "Lista"], "correct": "Cuento", "tip": "Tiene inicio, nudo y final."},
            {"question": "En una carta, ¿cómo saludás al empezar?", "options": ["Querido...", "Hola, chau", "Fin", "Gracias"], "correct": "Querido...", "tip": "Primero se saluda con cariño."},
            {"question": "¿Cuál de estas palabras imita un sonido?", "options": ["Perro", "¡Boom!", "Grande", "Rápido"], "correct": "¡Boom!", "tip": "Las onomatopeyas hacen ruido."},
            {"question": "¿Qué signo usamos para una pregunta?", "options": ["!", "¿?", ",", "."], "correct": "¿?", "tip": "En español las preguntas comienzan y terminan con el signo."},
            {"question": "¿Qué texto explica ingredientes y pasos?", "options": ["Cuento", "Receta", "Poema", "Aviso"], "correct": "Receta", "tip": "Tiene lista y instrucciones."},
            {"question": "¿Cómo se llama el que narra la historia?", "options": ["Autor", "Narrador", "Actor", "Director"], "correct": "Narrador", "tip": "Puede ser personaje o externo."},
            {"question": "¿Qué texto informa sobre un hecho real de hoy?", "options": ["Cuento", "Poema", "Noticia", "Juego"], "correct": "Noticia", "tip": "Responde qué, quién, cuándo, dónde."},
            {"question": "¿Qué parte de un cuento presenta a los personajes?", "options": ["Inicio", "Nudo", "Desenlace", "Título"], "correct": "Inicio", "tip": "Es el comienzo de la historia."},
            {"question": "¿Cuál de estas palabras rima con 'sol'?", "options": ["Casa", "Col", "Perro", "Mesa"], "correct": "Col", "tip": "Buscá el mismo sonido final."},
            {"question": "¿Qué texto tiene versos?", "options": ["Poema", "Receta", "Carta", "Instructivo"], "correct": "Poema", "tip": "Sus líneas se llaman versos."}
        ],
        "intermedio": [
            {"question": "¿Qué tipo de texto tiene personajes y un narrador?", "options": ["Receta", "Cuento", "Instructivo", "Noticia"], "correct": "Cuento", "tip": "Pensá en historias con principio y final."},
            {"question": "¿Qué parte de la carta dice adiós?", "options": ["Saludo", "Cuerpo", "Despedida", "Posdata"], "correct": "Despedida", "tip": "Se ubica antes de la firma."},
            {"question": "En un instructivo, ¿qué indican los verbos en infinitivo?", "options": ["Lugar", "Acción", "Tiempo", "Personaje"], "correct": "Acción", "tip": "Son los pasos a seguir."},
            {"question": "¿Cuál es un ejemplo de onomatopeya?", "options": ["Ruidoso", "¡Splash!", "Gigante", "Bella"], "correct": "¡Splash!", "tip": "Imita un sonido."},
            {"question": "¿Qué texto informa sobre un hecho real?", "options": ["Poema", "Noticia", "Cuento", "Historieta"], "correct": "Noticia", "tip": "Responde a qué, quién, cuándo, dónde."},
            {"question": "¿Qué signo de puntuación marca el final de una oración enunciativa?", "options": ["¿?", "!", ".", ","], "correct": ".", "tip": "Se usa para cerrar ideas."},
            {"question": "¿Qué recurso repite sonidos similares al inicio de palabras?", "options": ["Aliteración", "Metáfora", "Comparación", "Personificación"], "correct": "Aliteración", "tip": "Repite letras como la L en 'luz lenta'."},
            {"question": "¿Cómo se llama el que cuenta la historia?", "options": ["Protagonista", "Narrador", "Autor", "Lector"], "correct": "Narrador", "tip": "Puede ser un personaje o externo."},
            {"question": "¿Qué parte de un cuento presenta el conflicto?", "options": ["Inicio", "Nudo", "Desenlace", "Epílogo"], "correct": "Nudo", "tip": "Allí aparece el problema principal."},
            {"question": "¿Qué texto usa rimas y versos?", "options": ["Cuento", "Noticia", "Poema", "Receta"], "correct": "Poema", "tip": "Los versos se agrupan en estrofas."}
        ],
        "desafiante": [
            {"question": "¿Qué recurso literario compara dos cosas sin usar 'como'?", "options": ["Metáfora", "Simil", "Onomatopeya", "Hipérbole"], "correct": "Metáfora", "tip": "Une ideas para que imagines mejor."},
            {"question": "En una noticia, ¿qué información suele ir en el copete?", "options": ["Detalles mínimos", "Resumen del hecho", "Opinión personal", "Publicidad"], "correct": "Resumen del hecho", "tip": "Es lo primero que se lee."},
            {"question": "¿Cuál es la diferencia entre argumento y trama?", "options": ["Son iguales", "El argumento es general y la trama detalla", "La trama es general", "Ninguna"], "correct": "El argumento es general y la trama detalla", "tip": "Pensá en un mapa (argumento) y el viaje (trama)."},
            {"question": "¿Qué función cumplen las citas textuales en un informe?", "options": ["Decorar", "Aportar evidencia", "Hacer chistes", "Separar párrafos"], "correct": "Aportar evidencia", "tip": "Muestran que investigaste."},
            {"question": "¿Qué indica la voz pasiva en un texto?", "options": ["Quién recibe la acción", "Quién actúa", "Un sonido", "Un diálogo"], "correct": "Quién recibe la acción", "tip": "Ej: 'El cuadro fue pintado por Ana'."},
            {"question": "¿Cuál es la función de un organizador gráfico?", "options": ["Decorar", "Ordenar ideas", "Quitar datos", "Agregar chistes"], "correct": "Ordenar ideas", "tip": "Sirve para planificar antes de escribir."},
            {"question": "¿Qué diferencia hay entre noticia y crónica?", "options": ["Ninguna", "La crónica agrega opinión y orden cronológico", "La noticia inventa", "La crónica es más corta"], "correct": "La crónica agrega opinión y orden cronológico", "tip": "La noticia solo informa."},
            {"question": "¿Qué recurso permite exagerar una idea para darle fuerza?", "options": ["Metáfora", "Hipérbole", "Personificación", "Oxímoron"], "correct": "Hipérbole", "tip": "Ej: 'Te llamé un millón de veces'."},
            {"question": "¿Qué parte de una reseña describe la opinión del autor?", "options": ["Introducción", "Cuerpo", "Evaluación", "Ficha técnica"], "correct": "Evaluación", "tip": "Allí recomendás o no la obra."},
            {"question": "¿Por qué se usan conectores en un texto informativo?", "options": ["Para adornar", "Para unir ideas", "Para cambiar el tema", "Para borrar datos"], "correct": "Para unir ideas", "tip": "Palabras como 'además' guían al lector."}
        ]
    },
    "Cs. Naturales": {
        "facil": [
            {"question": "¿Qué parte del cuerpo usamos para respirar?", "options": ["Pulmones", "Corazón", "Estómago", "Pies"], "correct": "Pulmones", "tip": "Se inflan como globos."},
            {"question": "¿Cómo se llama el astro que nos da luz y calor?", "options": ["Luna", "Sol", "Tierra", "Marte"], "correct": "Sol", "tip": "Sale todos los días."},
            {"question": "¿Qué animal pone huevos?", "options": ["Gato", "Gallina", "Perro", "Conejo"], "correct": "Gallina", "tip": "Vive en el gallinero."},
            {"question": "¿Qué necesitamos las personas para vivir?", "options": ["Agua", "Arena", "Pintura", "Plástico"], "correct": "Agua", "tip": "Nuestro cuerpo es en gran parte agua."},
            {"question": "¿Cómo se llama el proceso del agua que se convierte en vapor?", "options": ["Lluvia", "Evaporación", "Hielo", "Granizo"], "correct": "Evaporación", "tip": "Ocurre con el calor."},
            {"question": "¿Qué parte de la planta absorbe agua?", "options": ["Flores", "Raíces", "Frutos", "Semillas"], "correct": "Raíces", "tip": "Están bajo tierra."},
            {"question": "¿Qué animal vive en el mar?", "options": ["Delfín", "Vaca", "Caballo", "Gato"], "correct": "Delfín", "tip": "Respira aire pero nada."},
            {"question": "¿Cómo se llama el gas que respiramos?", "options": ["Nitrógeno", "Oxígeno", "Helio", "Dióxido de carbono"], "correct": "Oxígeno", "tip": "Las plantas lo producen."},
            {"question": "¿Cuál es un ejemplo de alimento saludable?", "options": ["Gaseosa", "Manzana", "Golocina", "Papas fritas"], "correct": "Manzana", "tip": "Las frutas tienen vitaminas."},
            {"question": "¿Qué órgano late todo el tiempo?", "options": ["Pulmón", "Hígado", "Corazón", "Riñón"], "correct": "Corazón", "tip": "Bombea sangre."}
        ],
        "intermedio": [
            {"question": "¿Qué órgano bombea la sangre?", "options": ["Pulmón", "Hígado", "Corazón", "Estómago"], "correct": "Corazón", "tip": "Late todo el tiempo."},
            {"question": "¿Cómo se llama el proceso en el que las plantas producen su alimento?", "options": ["Respiración", "Fotosíntesis", "Digestión", "Evaporación"], "correct": "Fotosíntesis", "tip": "Usan luz del sol, agua y CO₂."},
            {"question": "¿Cuál es la estrella más cercana a la Tierra?", "options": ["Sirio", "Sol", "Polaris", "Vega"], "correct": "Sol", "tip": "Nos da luz y calor."},
            {"question": "¿Qué órgano nos permite respirar?", "options": ["Riñones", "Pulmones", "Huesos", "Piel"], "correct": "Pulmones", "tip": "Se inflan como globos."},
            {"question": "¿Qué estado del agua vemos en el hielo?", "options": ["Líquido", "Sólido", "Gaseoso", "Plasma"], "correct": "Sólido", "tip": "Mantiene forma propia."},
            {"question": "¿Cuál es un ejemplo de vertebrado?", "options": ["Caracol", "Gato", "Pulpo", "Mariposa"], "correct": "Gato", "tip": "Tienen columna vertebral."},
            {"question": "¿Qué gas respiramos del aire?", "options": ["Dióxido de carbono", "Helio", "Oxígeno", "Nitrógeno"], "correct": "Oxígeno", "tip": "Las plantas lo liberan."},
            {"question": "¿Cómo se llama el cambio de sólido a líquido?", "options": ["Condensación", "Fusión", "Sublimación", "Evaporación"], "correct": "Fusión", "tip": "Ocurre cuando el hielo se derrite."},
            {"question": "¿Qué parte de la planta absorbe agua del suelo?", "options": ["Flores", "Raíces", "Frutos", "Hojas"], "correct": "Raíces", "tip": "Son como pajitas subterráneas."},
            {"question": "¿Cuál es un ejemplo de mamífero acuático?", "options": ["Delfín", "Atún", "Medusa", "Tortuga"], "correct": "Delfín", "tip": "Respiran aire y amamantan a sus crías."}
        ],
        "desafiante": [
            {"question": "¿Por qué las hojas son verdes?", "options": ["Por la clorofila", "Por el agua", "Por la savia", "Por el sol"], "correct": "Por la clorofila", "tip": "Es un pigmento que capta luz."},
            {"question": "¿Qué parte del sistema respiratorio filtra el aire antes de llegar a los pulmones?", "options": ["Bronquios", "Tráquea", "Diafragma", "Clavícula"], "correct": "Tráquea", "tip": "Tiene pelitos que atrapan polvo."},
            {"question": "¿Qué planeta es conocido como el 'planeta rojo'?", "options": ["Mercurio", "Venus", "Marte", "Júpiter"], "correct": "Marte", "tip": "Su suelo tiene óxido de hierro."},
            {"question": "¿Cómo se llama el proceso en el que el agua pasa de gas a líquido?", "options": ["Sublimación", "Condensación", "Fusión", "Solidificación"], "correct": "Condensación", "tip": "Forma nubes y gotas."},
            {"question": "¿Qué sistema del cuerpo se encarga de enviar mensajes rápidos?", "options": ["Digestivo", "Nervioso", "Circulatorio", "Óseo"], "correct": "Nervioso", "tip": "Funciona con neuronas."},
            {"question": "¿Qué es un ecosistema?", "options": ["Un animal", "Un lugar donde interactúan seres vivos y ambiente", "Una planta", "Una nube"], "correct": "Un lugar donde interactúan seres vivos y ambiente", "tip": "Incluye clima, suelo, plantas y animales."},
            {"question": "¿Cuál es la función de los glóbulos blancos?", "options": ["Transportar oxígeno", "Defender el cuerpo", "Formar huesos", "Producir energía"], "correct": "Defender el cuerpo", "tip": "Son los soldados del sistema inmune."},
            {"question": "¿Qué ocurre en la mitosis?", "options": ["Respira la célula", "Se divide en dos células hijas", "Come la célula", "Se rompe el ADN"], "correct": "Se divide en dos células hijas", "tip": "Permite crecer y reparar tejidos."},
            {"question": "¿Por qué el sonido viaja más rápido en el agua que en el aire?", "options": ["El agua es más fría", "Porque las partículas están más juntas", "Hay más luz", "Se refleja"], "correct": "Porque las partículas están más juntas", "tip": "El sonido necesita un medio para vibrar."},
            {"question": "¿Cuál es la principal fuente de energía renovable en Argentina?", "options": ["Nuclear", "Eólica y solar", "Carbón", "Gas"], "correct": "Eólica y solar", "tip": "Aprovechan viento y sol sin agotarse."}
        ]
    },
    "Cs. Sociales": {
        "facil": [
            {"question": "¿Cómo se llama el lugar donde vivimos?", "options": ["País", "Planeta", "Barrio", "Todo"], "correct": "Barrio", "tip": "Es la zona cerca de casa."},
            {"question": "¿Qué símbolo patrio se canta?", "options": ["Bandera", "Himno", "Escudo", "Escarapela"], "correct": "Himno", "tip": "Tiene letra y música."},
            {"question": "¿Quién dirige una escuela?", "options": ["Director", "Intendente", "Presidente", "Comerciante"], "correct": "Director", "tip": "Coordina a los docentes."},
            {"question": "¿Qué usamos para orientarnos al norte, sur, este y oeste?", "options": ["Regla", "Brújula", "Libro", "Termómetro"], "correct": "Brújula", "tip": "Marca siempre el norte."},
            {"question": "¿Qué continente está en Argentina?", "options": ["Asia", "Europa", "Oceanía", "América"], "correct": "América", "tip": "Compartimos con muchos países."},
            {"question": "¿Qué profesión ayuda a curar a las personas?", "options": ["Médico", "Carpintero", "Piloto", "Actor"], "correct": "Médico", "tip": "Trabaja en hospitales o centros de salud."},
            {"question": "¿Qué transporte va por las vías?", "options": ["Auto", "Barco", "Tren", "Avión"], "correct": "Tren", "tip": "Sigue una línea de metal."},
            {"question": "¿Qué hacemos cuando votamos?", "options": ["Compramos", "Elegimos autoridades", "Jugamos", "Pintamos"], "correct": "Elegimos autoridades", "tip": "Es un derecho cívico."},
            {"question": "¿Qué es un mapa?", "options": ["Un cuento", "Una representación de un lugar", "Un juego", "Una canción"], "correct": "Una representación de un lugar", "tip": "Muestra ríos, ciudades y montañas."},
            {"question": "¿Qué fecha se celebra el Día de la Independencia en Argentina?", "options": ["25 de Mayo", "20 de Junio", "9 de Julio", "12 de Octubre"], "correct": "9 de Julio", "tip": "En 1816 declaramos ser libres."}
        ],
        "intermedio": [
            {"question": "¿Qué documento establece las reglas de un país?", "options": ["Factura", "Constitución", "Receta", "Agenda"], "correct": "Constitución", "tip": "Es la ley más importante."},
            {"question": "¿Cómo se llama a las personas que viven en un lugar?", "options": ["Vegetación", "Población", "Clima", "Relieve"], "correct": "Población", "tip": "Somos todos los habitantes."},
            {"question": "¿Qué invento facilitó el transporte marítimo?", "options": ["Semáforo", "Brújula", "Ascensor", "Radio"], "correct": "Brújula", "tip": "Ayuda a orientarse en el mar."},
            {"question": "¿Cuál es un ejemplo de recurso natural renovable?", "options": ["Carbón", "Petróleo", "Viento", "Hierro"], "correct": "Viento", "tip": "La naturaleza lo repone constantemente."},
            {"question": "¿Qué estudia la geografía?", "options": ["Hechos del pasado", "Lenguas", "El espacio y sus paisajes", "Números"], "correct": "El espacio y sus paisajes", "tip": "Observa relieves, climas y personas."},
            {"question": "¿Cómo se llama el poder que hace las leyes?", "options": ["Ejecutivo", "Judicial", "Legislativo", "Municipal"], "correct": "Legislativo", "tip": "Se reúne en el Congreso."},
            {"question": "¿Qué continente está al sur de Europa?", "options": ["Asia", "África", "Oceanía", "América"], "correct": "África", "tip": "Los separa el Mediterráneo."},
            {"question": "¿Cómo se llama el intercambio de productos entre regiones?", "options": ["Siembra", "Comercio", "Turismo", "Escritura"], "correct": "Comercio", "tip": "Puede ser local o internacional."},
            {"question": "¿Qué grupo defendía la independencia en 1810?", "options": ["Realistas", "Patriotas", "Piratas", "Exploradores"], "correct": "Patriotas", "tip": "Querían autogobernarse."},
            {"question": "¿Cuál es un ejemplo de símbolo patrio argentino?", "options": ["Escarapela", "Mate", "Asado", "Tango"], "correct": "Escarapela", "tip": "La usamos en fechas patrias."}
        ],
        "desafiante": [
            {"question": "¿Qué característica tiene un gobierno republicano?", "options": ["Un solo gobernante", "División de poderes", "Mandato vitalicio", "No hay elecciones"], "correct": "División de poderes", "tip": "Poder Ejecutivo, Legislativo y Judicial."},
            {"question": "¿Por qué la Revolución Industrial cambió la población urbana?", "options": ["No hubo cambios", "Porque generó trabajo en las ciudades", "Porque cerró las fábricas", "Porque prohibió el comercio"], "correct": "Porque generó trabajo en las ciudades", "tip": "Muchas personas migraron desde el campo."},
            {"question": "¿Qué recurso natural no renovable se forma durante millones de años?", "options": ["Petróleo", "Viento", "Energía solar", "Agua"], "correct": "Petróleo", "tip": "Se usa para combustibles."},
            {"question": "¿Qué es la globalización?", "options": ["Un deporte", "La conexión entre países a nivel económico y cultural", "Una fiesta", "Un río"], "correct": "La conexión entre países a nivel económico y cultural", "tip": "Permite que ideas y productos viajen rápido."},
            {"question": "¿Cuál es una consecuencia de la deforestación?", "options": ["Más oxígeno", "Pérdida de biodiversidad", "Más lluvia", "Bosques saludables"], "correct": "Pérdida de biodiversidad", "tip": "Menos árboles = menos hábitats."},
            {"question": "¿Qué describe un climograma?", "options": ["Animales", "Temperaturas y precipitaciones", "Transportes", "Lenguas"], "correct": "Temperaturas y precipitaciones", "tip": "Tiene barras y líneas."},
            {"question": "¿Cuál fue la importancia de la Asamblea del Año XIII?", "options": ["Inventó la imprenta", "Declaró un himno y escudo, avanzó en libertad de vientres", "Fundó escuelas", "Organizó el fútbol"], "correct": "Declaró un himno y escudo, avanzó en libertad de vientres", "tip": "Fue un paso hacia la independencia completa."},
            {"question": "¿Qué midió la Primera Junta al asumir en 1810?", "options": ["La población", "La cantidad de impuestos", "El valor del peso", "La producción agrícola"], "correct": "La cantidad de impuestos", "tip": "Necesitaban financiamiento para gobernar."},
            {"question": "¿Qué significa soberanía popular?", "options": ["Gobierna el rey", "El poder reside en el pueblo", "Gobierna un ejército", "Gobierna otro país"], "correct": "El poder reside en el pueblo", "tip": "Las decisiones se toman por votación."},
            {"question": "¿Cuál fue una causa económica de la independencia americana?", "options": ["Abundancia de oro", "Deseo de comerciar sin restricciones españolas", "Escasez de ideas", "La radio"], "correct": "Deseo de comerciar sin restricciones españolas", "tip": "Las colonias querían vender directamente."}
        ]
    },
    "Ed. Física": {
        "facil": [
            {"question": "¿Qué parte del cuerpo movés cuando saltás?", "options": ["Piernas", "Orejas", "Pestañas", "Nariz"], "correct": "Piernas", "tip": "Te ayudan a despegar."},
            {"question": "¿Qué debés hacer antes de correr?", "options": ["Estirar", "Dormir", "Comer golosinas", "Ver TV"], "correct": "Estirar", "tip": "Calentar evita lesiones."},
            {"question": "¿Qué bebida hidrata mejor?", "options": ["Gaseosa", "Agua", "Jugo artificial", "Gaseosa de cola"], "correct": "Agua", "tip": "Siempre llevá tu botellita."},
            {"question": "¿Qué objeto se usa para jugar al fútbol?", "options": ["Raqueta", "Pelota", "Red", "Disco"], "correct": "Pelota", "tip": "Se patea."},
            {"question": "¿Qué valor practicás al esperar tu turno?", "options": ["Paciencia", "Ruido", "Tristeza", "Olvido"], "correct": "Paciencia", "tip": "Así todos juegan."},
            {"question": "¿Qué postura es correcta al sentarse?", "options": ["Espalda recta", "Hombros caídos", "Cabeza colgando", "Sin apoyarse"], "correct": "Espalda recta", "tip": "Apoyá la espalda en el respaldo."},
            {"question": "¿Qué elemento se usa para saltar la soga?", "options": ["Soga", "Pelota", "Palo", "Aro"], "correct": "Soga", "tip": "Coordiná brazos y piernas."},
            {"question": "¿Qué sentido usamos para mantener el equilibrio?", "options": ["Vista", "Oído", "Tacto", "Todos ayudan"], "correct": "Todos ayudan", "tip": "El cuerpo trabaja en equipo."},
            {"question": "¿Qué parte del cuerpo fortalece andar en bici?", "options": ["Manos", "Piernas", "Orejas", "Nariz"], "correct": "Piernas", "tip": "Pedalear es gran ejercicio."},
            {"question": "¿Qué juego necesita una pelota chica y una red baja?", "options": ["Tenis", "Handball", "Ping pong", "Vóley"], "correct": "Ping pong", "tip": "Se juega con paletas."}
        ],
        "intermedio": [
            {"question": "¿Cuál es una actividad aeróbica?", "options": ["Leer", "Correr", "Dormir", "Pintar"], "correct": "Correr", "tip": "Hace trabajar corazón y pulmones."},
            {"question": "¿Qué parte se debe estirar antes de saltar?", "options": ["Dedos", "Piernas", "Orejas", "Ceja"], "correct": "Piernas", "tip": "Son las que impulsan el salto."},
            {"question": "¿Cómo se llama el ejercicio de mantenerse en una sola pierna?", "options": ["Resistencia", "Equilibrio", "Velocidad", "Fuerza"], "correct": "Equilibrio", "tip": "Imaginá que sos un flamenco."},
            {"question": "¿Cuál es una señal de que se debe hidratar el cuerpo?", "options": ["Cansancio", "Sueño", "Hambre", "Frío"], "correct": "Cansancio", "tip": "Tomá agua antes y después de jugar."},
            {"question": "¿Qué objeto se usa para medir el tiempo en carreras?", "options": ["Brújula", "Cronómetro", "Linterna", "Pelota"], "correct": "Cronómetro", "tip": "Cuenta segundos con precisión."},
            {"question": "¿Cuál es un ejemplo de juego cooperativo?", "options": ["Escondidas", "Carrera de postas", "Rayuela", "Saltar la soga"], "correct": "Carrera de postas", "tip": "Necesitás a tu equipo."},
            {"question": "¿Qué músculo fortalece hacer abdominales?", "options": ["Cuádriceps", "Bíceps", "Abdomen", "Gemelos"], "correct": "Abdomen", "tip": "Protege la espalda."},
            {"question": "¿Cuál es una postura correcta al sentarse?", "options": ["Espalda recta", "Hombros caídos", "Cabeza hacia abajo", "Piernas cruzadas"], "correct": "Espalda recta", "tip": "Apoyá toda la espalda en el respaldo."},
            {"question": "¿Qué elemento se usa en vóley para separar los equipos?", "options": ["Arco", "Red", "Aro", "Paralelas"], "correct": "Red", "tip": "La pelota debe pasar por encima."},
            {"question": "¿Qué valor se refuerza al respetar turnos en un juego?", "options": ["Paciencia", "Tristeza", "Ruido", "Olvido"], "correct": "Paciencia", "tip": "Esperar turno mantiene el juego ordenado."}
        ],
        "desafiante": [
            {"question": "¿Qué capacidad mejora el entrenamiento interválico?", "options": ["Flexibilidad", "Resistencia aeróbica", "Reacción", "Ninguna"], "correct": "Resistencia aeróbica", "tip": "Alterna tramos rápidos y lentos."},
            {"question": "¿Qué músculo trabaja el ejercicio de plancha?", "options": ["Abdominales", "Gemelos", "Trapecio", "Cuádriceps"], "correct": "Abdominales", "tip": "Mantiene el cuerpo firme como tabla."},
            {"question": "¿Qué componente del entrenamiento desarrolla la agilidad?", "options": ["Series de velocidad", "Estiramiento suave", "Respiración", "Relajación"], "correct": "Series de velocidad", "tip": "Frena, gira y vuelve a arrancar."},
            {"question": "¿Qué sucede si elongás solo 5 segundos cada músculo?", "options": ["Es suficiente", "No alcanza para relajar", "Mejora mucho", "Es peligroso"], "correct": "No alcanza para relajar", "tip": "Necesitás al menos 20 segundos."},
            {"question": "¿Qué indica tu frecuencia cardíaca máxima aproximada?", "options": ["220 - edad", "Edad + 20", "Edad x 2", "120 fijo"], "correct": "220 - edad", "tip": "Sirve para medir el esfuerzo."},
            {"question": "¿Cuál es un ejemplo de ejercicio pliométrico?", "options": ["Saltar cajones", "Marchar", "Caminar", "Balancearse"], "correct": "Saltar cajones", "tip": "Impulsa músculos enérgicamente."},
            {"question": "¿Qué cualidad física trabaja una carrera de 60 metros?", "options": ["Fuerza máxima", "Velocidad", "Resistencia", "Flexibilidad"], "correct": "Velocidad", "tip": "Se corre lo más rápido posible."},
            {"question": "¿Por qué se recomienda hidratarse con sorbos frecuentes?", "options": ["Para cansarse", "Para evitar calambres y reponer lo perdido", "Para enfriar los pies", "Para dormir"], "correct": "Para evitar calambres y reponer lo perdido", "tip": "El cuerpo elimina agua al sudar."},
            {"question": "¿Qué cualidad desarrolla el trabajo con bandas elásticas?", "options": ["Fuerza", "Olfato", "Equilibrio", "Todos"], "correct": "Fuerza", "tip": "Podés graduar la intensidad."},
            {"question": "¿Qué valor deportivo se fortalece al animar a tu equipo incluso si pierden?", "options": ["Respeto", "Desigualdad", "Tristeza", "Ruido"], "correct": "Respeto", "tip": "El juego limpio vale más que el resultado."}
        ]
    },
    "Inglés": {
        "facil": [
            {"question": "¿Cómo se dice 'hola' en inglés?", "options": ["Bye", "Hello", "Thanks", "Dog"], "correct": "Hello", "tip": "Se pronuncia jeló."},
            {"question": "¿Cuál es el color 'red'?", "options": ["Azul", "Rojo", "Verde", "Amarillo"], "correct": "Rojo", "tip": "Pensá en una manzana roja."},
            {"question": "¿Cómo se dice 'gracias'?", "options": ["Please", "Thanks", "Sorry", "Hello"], "correct": "Thanks", "tip": "También podés decir Thank you."},
            {"question": "¿Cuál es el plural de 'cat'?", "options": ["Cates", "Cats", "Catos", "Cat"], "correct": "Cats", "tip": "Solo agregá una s."},
            {"question": "¿Qué palabra significa 'libro'?", "options": ["Book", "Bag", "Box", "Bike"], "correct": "Book", "tip": "Las cuatro empiezan igual."},
            {"question": "¿Cómo se dice 'sí'?", "options": ["No", "Yes", "Good", "See"], "correct": "Yes", "tip": "Se pronuncia 'ies'."},
            {"question": "¿Cuál es la traducción de 'house'?", "options": ["Casa", "Auto", "Árbol", "Silla"], "correct": "Casa", "tip": "Rima con mouse."},
            {"question": "¿Qué pronombre usamos para hablar de nosotros?", "options": ["He", "She", "We", "They"], "correct": "We", "tip": "Incluye a quien habla."},
            {"question": "¿Cómo se dice 'perro'?", "options": ["Cat", "Bird", "Dog", "Fish"], "correct": "Dog", "tip": "Suena a 'dog'."},
            {"question": "¿Qué significa 'thank you'?", "options": ["Por favor", "Hola", "Gracias", "Adiós"], "correct": "Gracias", "tip": "Úsalo al recibir ayuda."}
        ],
        "intermedio": [
            {"question": "¿Cómo se dice ""gato"" en inglés?", "options": ["Dog", "Cat", "Cow", "Duck"], "correct": "Cat", "tip": "Suena parecido a la palabra en español."},
            {"question": "¿Cuál es el plural de ""bus""?", "options": ["Buses", "Buss", "Busies", "Busez"], "correct": "Buses", "tip": "Agregá -es cuando termina en s."},
            {"question": "¿Cómo se traduce ""blue""?", "options": ["Rojo", "Azul", "Verde", "Amarillo"], "correct": "Azul", "tip": "Piénsalo como el color del cielo."},
            {"question": "¿Qué pronombre reemplaza a ""María y yo""?", "options": ["We", "They", "She", "He"], "correct": "We", "tip": "Es la forma para nosotros."},
            {"question": "¿Cómo se dice ""gracias"" en inglés?", "options": ["Please", "Hello", "Thanks", "Bye"], "correct": "Thanks", "tip": "También podés decir Thank you."},
            {"question": "¿Cuál es el pasado de ""play""?", "options": ["Played", "Playd", "Plays", "Playsed"], "correct": "Played", "tip": "Los verbos regulares suman -ed."},
            {"question": "¿Qué significa ""Good morning""?", "options": ["Buenas noches", "Buenos días", "Hola", "Chau"], "correct": "Buenos días", "tip": "Se usa por la mañana."},
            {"question": "¿Cuál es la forma correcta para decir ""ella está feliz""?", "options": ["She is happy", "She are happy", "She happy", "She be happy"], "correct": "She is happy", "tip": "She va con el verbo is."},
            {"question": "¿Cómo se dice ""libro"" en inglés?", "options": ["Book", "Box", "Bag", "Bike"], "correct": "Book", "tip": "Las cuatro empiezan con B, ¡leé bien!"},
            {"question": "¿Qué palabra completa la frase ""I ___ pizza""?", "options": ["like", "likes", "liked", "liking"], "correct": "like", "tip": "Con I el verbo queda en su forma base."}
        ],
        "desafiante": [
            {"question": "¿Cuál es el pasado de 'to eat'?", "options": ["Eat", "Eated", "Ate", "Eaten"], "correct": "Ate", "tip": "Es un verbo irregular."},
            {"question": "¿Cómo traducís 'She has been studying'?", "options": ["Ella estudia", "Ella estuvo estudiando", "Ella estudió ayer", "Ella estudiará"], "correct": "Ella estuvo estudiando", "tip": "Es un presente perfecto continuo."},
            {"question": "¿Cuál es el comparativo de 'happy'?", "options": ["More happy", "Happier", "Most happy", "Happyer"], "correct": "Happier", "tip": "Si termina en y, se cambia por ier."},
            {"question": "Completá: 'If it rains, we ___ inside.'", "options": ["stay", "stays", "stayed", "staying"], "correct": "stay", "tip": "En condicional tipo 0 la forma es simple."},
            {"question": "¿Cuál es el sinónimo de 'clever'?", "options": ["Smart", "Slow", "Angry", "Tall"], "correct": "Smart", "tip": "Ambas significan inteligente."},
            {"question": "¿Qué significa 'by the way'?", "options": ["De todos modos", "Por cierto", "Sin embargo", "Porque sí"], "correct": "Por cierto", "tip": "Se usa para agregar un dato."},
            {"question": "¿Qué tiempo verbal expresa acciones futuras planificadas?", "options": ["Past simple", "Present continuous", "Present perfect", "Past continuous"], "correct": "Present continuous", "tip": "Se usa con expresiones como 'tomorrow'."},
            {"question": "¿Cómo se dice 'ella ha estado aquí desde las 8'?", "options": ["She is here since 8", "She has been here since 8", "She was here since 8", "She be here since 8"], "correct": "She has been here since 8", "tip": "Usá present perfect con since."},
            {"question": "¿Qué phrasal verb significa 'investigar'?", "options": ["Look after", "Look up", "Look into", "Look for"], "correct": "Look into", "tip": "Se usa para examinar algo."},
            {"question": "¿Cómo se forma el plural de 'child'?", "options": ["Childs", "Children", "Chields", "Childer"], "correct": "Children", "tip": "Es un plural irregular muy común."}
        ]
    }
}


def _extract_json_payload(text: str) -> dict:
    if not text:
        return {}
    match = re.search(r"```(?:json)?(.*?)```", text, re.DOTALL)
    if match:
        text = match.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def _normalize_questions(raw_questions):
    normalized = []
    for item in raw_questions:
        question = item.get("question", "").strip()
        options = [opt.strip() for opt in item.get("options", []) if opt.strip()]
        correct = item.get("correct", "").strip()
        tip = item.get("tip", "").strip() or "Recordá la pista de GATTO."

        if not question or len(options) < 2 or not correct:
            continue

        if correct not in options:
            options = options[:3]
            options.append(correct)

        normalized.append({
            "question": question,
            "options": options[:4],
            "correct": correct,
            "tip": tip,
        })

    return normalized


def get_questions_for_subject(subject: str, level: str):
    level_key = level if level in DIFFICULTIES else "facil"
    prompt = TEST_PROMPT_TEMPLATE.format(
        subject=subject,
        level_text=DIFFICULTY_DESCRIPTIONS[level_key]
    )

    try:
        quiz_model = genai.GenerativeModel("gemini-2.0-flash-exp")
        response = quiz_model.generate_content(prompt, timeout=30)
        payload = _extract_json_payload(getattr(response, "text", ""))
        questions = _normalize_questions(payload.get("questions", []))
    except Exception as e:
        print(f"Error generando preguntas: {e}")
        questions = []

    if len(questions) >= 10:
        return questions[:10]

    subject_data = FALLBACK_TESTS.get(subject, FALLBACK_TESTS["Matemática"])
    return subject_data[level_key]

@app.route("/", methods=["GET"]) 
def home():
    return render_template("index.html")


@app.route("/buscar", methods=["POST"]) 
def buscar():
    duda = request.form.get("duda", "").strip()
    if not duda:
        return redirect(url_for('home'))
    
    # Validación básica
    if len(duda) < 3 or len(duda) > 500:
        return redirect(url_for('home'))

    try:
        full_prompt = PROMPT_BASE + "\n\nDuda del alumno: " + duda
        tutor_model = genai.GenerativeModel("gemini-2.5-flash")
        response = tutor_model.generate_content(full_prompt, timeout=30)
        respuesta = getattr(response, 'text', '')
        
        if not respuesta:
            respuesta = "<p>⚠️ No pude generar una respuesta. Intenta reformular tu pregunta.</p>"
    except Exception as e:
        print(f"Error al procesar búsqueda: {e}")
        respuesta = "<p>⚠️ Ocurrió un error al procesar tu pregunta. Por favor, intenta más tarde.</p>"

    return render_template("respuesta.html", duda=duda, respuesta=respuesta)


@app.route("/test")
def test():
    materia = request.args.get("materia", "Matemática")
    if materia not in FALLBACK_TESTS:
        materia = "Matemática"

    nivel = request.args.get("nivel", "facil").lower()
    if nivel not in DIFFICULTIES:
        nivel = "facil"

    try:
        preguntas = get_questions_for_subject(materia, nivel)
    except Exception as e:
        print(f"Error cargando preguntas: {e}")
        preguntas = FALLBACK_TESTS[materia][nivel]

    return render_template(
        "test.html",
        materia=materia,
        materias=list(FALLBACK_TESTS.keys()),
        preguntas=preguntas,
        nivel=nivel,
        nivel_label=DIFFICULTIES[nivel],
    )

if __name__ == "__main__":
    # Configuración para desarrollo
    app.run(debug=os.getenv("FLASK_DEBUG", "False").lower() == "true")
