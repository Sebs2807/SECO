# SECO / Sanofi – Django App

Proyecto Django con una app `core` para gestión y visualización (facturas, gráficas) y configuración lista para despliegue gratuito en Render.

## Requisitos
- Python 3.11+
- Windows PowerShell (o cualquier shell)

## Estructura
- `sanofi/` proyecto Django raíz
  - `manage.py` comandos de administración
  - `core/` app principal (models, views, templates, static)
  - `sanofi/settings.py` configuración del proyecto
  - `requirements.txt` dependencias
  - `Procfile` comando de arranque en producción
  - `render.yaml` configuración opcional para Render
  - `db.sqlite3` base de datos local

## Configuración local
```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r sanofi\requirements.txt
python sanofi\manage.py migrate
python sanofi\manage.py collectstatic --noinput
python sanofi\manage.py runserver
```
- App disponible en `http://127.0.0.1:8000/`

## Variables de entorno
- `DJANGO_SETTINGS_MODULE=sanofi.settings`
- `ALLOWED_HOSTS` (por defecto `*`; usa tu dominio en producción)
- `PYTHON_VERSION=3.11` (Render)

## Pruebas
Hay tests en `sanofi/core/tests.py` y un script `test_reconciliation.py`.
```powershell
python sanofi\manage.py test
```

## Despliegue (Render – plan free)
1. Subir el repo a GitHub.
2. En Render: New → Web Service → Conectar el repo.
3. Root dir: `proyecto/sanofi`.
4. Build Command (multilínea):
   ```
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```
5. Start Command: Render detecta `Procfile` → `web: gunicorn sanofi.wsgi:application --bind 0.0.0.0:$PORT`.
6. Env Vars: `DJANGO_SETTINGS_MODULE=sanofi.settings`, `PYTHON_VERSION=3.11`, `ALLOWED_HOSTS=<tu-servicio>.onrender.com`.

Alternativa: usar `render.yaml` (ya incluido) y elegir “Use render.yaml”.

## Notas
- Whitenoise sirve los estáticos en producción.
- SQLite es suficiente para demos; para producción considera PostgreSQL.

## Licencia
Uso interno/educativo.