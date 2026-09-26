# MineriaGrupo10
Tarea semana 7 mineria de datos

## Reglas para la integración del trabajo

El proyecto utilizará un flujo de trabajo basado en un **Git Flow básico**. Este proceso permite desarrollar los cambios de forma organizada, revisarlos antes de integrarlos y mantener una versión estable del proyecto.

### Rama `main`

- Representa la versión estable del proyecto.
- No se permiten commits ni `push` directos sobre esta rama.
- Los cambios solo pueden integrarse mediante un **Pull Request**.
- La rama está protegida mediante las reglas configuradas en GitHub.

### Rama `develop`

- Es la rama principal de integración del desarrollo.
- No se permiten commits ni `push` directos sobre esta rama.
- Los cambios solo pueden integrarse mediante un **Pull Request**.
- La rama también está protegida mediante las reglas configuradas en GitHub.

### Ramas `feature`

- Cada nueva funcionalidad, corrección o tarea debe desarrollarse en una rama independiente.
- Las ramas `feature` siempre deben crearse a partir de `develop`.
- Utilizar una nomenclatura clara, por ejemplo:

```text
feature/nombre-funcionalidad
```

Ejemplos:

```text
feature/login
feature/registro-usuarios
feature/dashboard
```

### Proceso para iniciar una tarea

Antes de crear una rama `feature`, se debe actualizar la rama `develop` local para trabajar sobre la versión más reciente del proyecto:

```bash
git checkout develop
git pull origin develop
git checkout -b feature/nombre-funcionalidad
```

### Desarrollo y commits

- Los cambios deben realizarse únicamente en la rama `feature`.
- Realizar commits pequeños y descriptivos.
- No realizar commits directamente sobre `main` o `develop`.

Ejemplo:

```bash
git add .
git commit -m "Agrega validación del formulario de registro"
git push origin feature/nombre-funcionalidad
```

### Integración hacia `develop`

- Cuando la funcionalidad esté terminada, se debe subir la rama al repositorio remoto.
- Crear un **Pull Request** desde `feature/nombre-funcionalidad` hacia `develop`.
- El Pull Request debe ser revisado antes de realizar el merge.
- Resolver comentarios o conflictos antes de completar la integración.

```text
feature/*
	 │
	 │ Pull Request
	 ▼
 develop
```

### Integración hacia `main`

- La rama `main` debe recibir cambios únicamente desde `develop`.
- Cuando se tenga una versión estable lista para entregar o publicar, crear un **Pull Request** desde `develop` hacia `main`.
- No realizar commits ni merges directos sobre `main`.

```text
feature/*
	 │
	 │ Pull Request
	 ▼
 develop
	 │
	 │ Pull Request
	 ▼
	main
```

### Reglas generales

- Mantener actualizada la rama `develop` antes de crear una nueva rama.
- Cada rama `feature` debe corresponder a una tarea o funcionalidad específica.
- No trabajar directamente sobre `main` o `develop`.
- Todo cambio debe pasar por Pull Request.
- Antes de crear un Pull Request, verificar que el proyecto compile y funcione correctamente.
- Resolver los conflictos antes de completar el merge.
- Utilizar nombres de ramas y mensajes de commit descriptivos.

### Resumen del flujo

1. Actualizar `develop`.
2. Crear una rama `feature` desde `develop`.
3. Realizar el desarrollo y los commits en la rama `feature`.
4. Subir la rama `feature` a GitHub.
5. Crear un Pull Request hacia `develop`.
6. Revisar y realizar el merge.
7. Cuando `develop` tenga una versión estable, crear un Pull Request hacia `main`.

## Proyecto: Presuntos Homicidios en Colombia, 2015 a 2024

Aplicación web en Flask y Bootstrap con el análisis exploratorio del conjunto de datos
[Presuntos Homicidios. Colombia, 2015 a 2024. Cifras definitivas](https://www.datos.gov.co/Justicia-y-Derecho/Presuntos-Homicidios-Colombia-2015-a-2024-Cifras-d/vtub-3de2/about_data)
publicado por el Instituto Nacional de Medicina Legal y Ciencias Forenses.

### Estructura

```text
app.py                  Rutas de la aplicación
datos.py                Carga y limpieza del conjunto de datos (compartido por todas las dimensiones)
data/                   CSV original comprimido en gzip (pandas lo lee directamente)
templates/base.html     Plantilla base con Bootstrap, fuentes, íconos y el menú de navegación
templates/_encabezado_dimension.html  Encabezado común (título, integrante y pregunta) de cada dimensión
templates/*.html        Inicio y una página por dimensión
static/css/styles.css   Identidad visual (tema oscuro, animaciones, tarjetas)
static/js/main.js       Animaciones al hacer scroll, contadores y botón volver arriba
requirements.txt        Dependencias
```

Cada dimensión tiene su ruta en `app.py` y su plantilla en `templates/`. Las plantillas extienden
`base.html` (`{% extends "base.html" %}`) para conservar el menú y la identidad visual.
Los datos se obtienen con `from datos import cargar_datos`.

La lista `DIMENSIONES` de `app.py` alimenta el menú, las tarjetas del inicio y el encabezado de cada
página. Para construir un tablero basta con reemplazar el bloque «Tablero en construcción» de la
plantilla de la dimensión. Clases útiles de `styles.css`:

- `tarjeta`: contenedor de vidrio para gráficas, indicadores o textos.
- `aparecer`: animación de entrada al hacer scroll (retraso opcional con `style="--retraso: .2s"`).
- `btn-neon`, `btn-contorno`: botones del sitio.
- Los componentes de Bootstrap `card`, `table` y `form-select` ya están adaptados al tema oscuro.

### Ejecución local

Requiere Python 3.11 o superior.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux / macOS
pip install -r requirements.txt
python app.py
```

Abrir http://127.0.0.1:5000 en el navegador.
