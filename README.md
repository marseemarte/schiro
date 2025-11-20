# 🐱 GATTO - Aprendé Jugando

Una plataforma web educativa interactiva que utiliza IA para ayudar a estudiantes de primaria (7-12 años) con sus tareas escolares y ofrece tests interactivos para practicar diferentes materias.

## ✨ Características

- 🤖 **Asistente IA Inteligente**: Responde preguntas escolares con explicaciones claras y estructuradas
- 🎮 **Tests Interactivos**: 10 preguntas con 3 niveles de dificultad en 6 materias
- 📚 **Abecedario Mágico**: Aprende cada letra con palabras y emojis
- 🎨 **Diseño Amigable**: Interfaz colorida y accesible para niños
- ⚡ **Respuestas Estructuradas**: Explicaciones técnicas, simples, ejemplos y desafíos

## 🚀 Instalación Rápida

### Requisitos
- Python 3.8+
- pip
- Git

### Pasos

1. **Clonar el repositorio**
```bash
git clone https://github.com/marseemarte/schiro.git
cd schiro
```

2. **Crear y activar entorno virtual** (recomendado)
```bash
# En Windows
python -m venv venv
venv\Scripts\activate

# En macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
# Copiar el archivo ejemplo
cp .env.example .env

# Editar .env y agregar tu API key de Gemini
# GEMINI_API_KEY=tu_api_key_aqui
```

5. **Obtener API key de Gemini**
- Ve a https://makersuite.google.com/app/apikey
- Crea una nueva API key
- Cópiala en tu archivo `.env`

6. **Ejecutar la aplicación**
```bash
python app.py
```

7. **Abrir en el navegador**
```
http://localhost:5000
```

## 📚 Materias y Niveles

### Materias Disponibles
- 📐 Matemática
- 📖 PDL (Prácticas del Lenguaje)
- 🌍 Ciencias Naturales
- 🏛️ Ciencias Sociales
- 🏃 Educación Física
- 🌎 Inglés

### Niveles de Dificultad
- 🟢 **Fácil**: Preguntas básicas con conceptos simples
- 🟡 **Intermedio**: Requieren algo más de razonamiento
- 🔴 **Desafiante**: Pensamiento crítico y conexión de ideas

## 🏗️ Estructura del Proyecto

```
schiro/
├── app.py                      # Servidor Flask
├── requirements.txt            # Dependencias Python
├── .env.example               # Template de variables de entorno
├── .gitignore                 # Archivos a ignorar en Git
├── templates/
│   ├── index.html            # Página principal
│   ├── respuesta.html        # Página de respuestas del tutor
│   └── test.html             # Página de tests
└── static/
    ├── css/
    │   ├── index.css         # Estilos principales
    │   └── respuestas.css    # Estilos del slider
    ├── js/
    │   └── index.js          # Lógica de frontend
    └── img/
        ├── gatito.png
        ├── respuesta_técnica.png
        └── ... (otras imágenes)
```

## 🔧 Tecnologías

- **Backend**: Flask (Python)
- **IA**: Google Generative AI (Gemini 2.0 Flash)
- **Frontend**: HTML5, CSS3, JavaScript vanilla
- **Styling**: Tailwind CSS, CSS personalizado
- **Fuentes**: Google Fonts (Chewy, Nunito)

## 💻 Uso

### Para Estudiantes
1. Dirígete a la página principal
2. Escribe tu pregunta en el buscador o elige una sugerencia
3. Obtén una respuesta estructurada del "Profesor GATTO"
4. Navega entre secciones con los botones de siguiente/anterior
5. O elige un test en la sección "Aprendé Jugando"

### Para Desarrolladores

#### Endpoints Principales
- `GET /` - Página de inicio
- `POST /buscar` - Procesa una pregunta y retorna respuesta de IA
- `GET /test` - Carga un test con preguntas

#### Variables de Entorno
```
GEMINI_API_KEY    - Tu clave de API de Google Gemini
FLASK_ENV         - development o production
FLASK_DEBUG       - True/False
```

## 🎨 Paleta de Colores

- 🟡 Amarillo: `#f6c21a` (principal)
- 🔵 Azul: `#39a4ff`
- 🩷 Rosa: `#ff6ec7`
- 🟢 Verde: `#7ac943`
- 🟠 Naranja: `#ffa221`
- ⚪ Fondo: `#fff9e8`

## 🔒 Seguridad

- ✅ API key protegida en variables de entorno
- ✅ No se expone información sensible en GitHub
- ✅ Validación básica de inputs
- ✅ Contenido generado por IA supervisado

## 🚧 Mejoras Futuras

- [ ] Sistema de cuentas de usuario
- [ ] Guardado de historial de búsquedas
- [ ] Estadísticas de desempeño en tests
- [ ] Sistema de puntos y logros
- [ ] Modo offline
- [ ] Tema oscuro
- [ ] Más idiomas

## 📝 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Haz un fork del proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📧 Contacto

- **Equipo**: marseemarte
- **Email**: contacto@schiro.edu
- **GitHub**: https://github.com/marseemarte/schiro

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo LICENSE para más detalles.

---

**Hecho con ❤️ para estudiantes de primaria**
