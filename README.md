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
