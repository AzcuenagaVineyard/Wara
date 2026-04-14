# WARA — Sistema de Análisis de Tractores
## New Holland TT3880F · Finca Azcuénaga

---

## Archivos del sistema

| Archivo | Función |
|---|---|
| `parse_wara.py` | Parsea PDFs de WARA y guarda en la base de datos |
| `server_wara.py` | Servidor local que alimenta el dashboard |
| `dashboard.html` | Dashboard de análisis (abrir en el navegador) |
| `wara.db` | Base de datos SQLite (se crea automáticamente) |
| `Azcue_nagaVineyard.kml` | Mapa con los sectores de la finca |
| `pdfs/` | Carpeta donde colocar los PDFs de WARA |

---

## Instalación inicial (una sola vez)

### 1. Instalar Python 3 (si no está instalado)
Abrí la Terminal y escribí:
```
python3 --version
```
Si no está instalado, descargalo de https://python.org/downloads/

### 2. Instalar dependencias
```
pip3 install pdfplumber shapely
```

### 3. Colocar los archivos
Creá una carpeta en tu Mac, por ejemplo:
```
~/Documents/WARA/
```
Y copiá todos estos archivos ahí:
- `parse_wara.py`
- `server_wara.py`  
- `dashboard.html`
- `Azcue_nagaVineyard.kml`
- Creá una subcarpeta `pdfs/`

---

## Uso diario

### Paso 1 — Agregar nuevos PDFs
Cuando llegue el reporte de WARA por email, guardá el PDF en la carpeta `pdfs/`.

### Paso 2 — Importar a la base de datos
Abrí la Terminal, navegá a tu carpeta WARA y ejecutá:
```
cd ~/Documents/WARA
python3 parse_wara.py pdfs/
```
El script procesa solo los archivos nuevos (los ya importados se saltan automáticamente).

### Paso 3 — Abrir el dashboard
En la misma Terminal:
```
python3 server_wara.py
```
Luego abrí tu navegador y entrá a:
```
http://localhost:8765
```

Para cerrar el servidor cuando terminés: `Ctrl + C` en la Terminal.

---

## Funcionalidades del dashboard

| Pestaña | Qué muestra |
|---|---|
| **Resumen** | KPIs totales, gráfico de distancia y movimiento vs inactividad |
| **Diario** | Tabla completa día a día con % de inactividad |
| **Inactividad** | Análisis de ralentí por día de semana, detenciones más largas |
| **Sectores** | Tiempo por sector de la finca (requiere coincidencia GPS/KML) |
| **Patrones** | Uso por día de semana, distribución de horarios de arranque/término |

---

## Sectores de la finca (13 en total)

El sistema reconoce automáticamente estos sectores cuando los stops del tractor coinciden con las coordenadas GPS del KML:

- Malbec 2012 · Malbec 2018 · Malbec Injerto
- Cab Franc 1990 · Cab Franc Injerto
- Petit Verdot · Merlot
- Cab Sauv N (tri) · Cab Sauv S (rect) · Cab Sauv 2027
- Casa Ortiz · Casa Hugas · Represa

Los stops fuera de estos polígonos se etiquetan como **Tránsito**.

> **Nota:** Los PDFs de WARA incluyen nombres de calles pero no coordenadas GPS.
> El sistema usa un mapa de coordenadas conocidas para los puntos frecuentes de la finca.
> Para mejorar la cobertura de sectores, se pueden agregar más coordenadas al archivo
> `geo_cache` en la base de datos.

---

## Solución de problemas

**"No PDF files found"** → Verificá que los PDFs estén en la carpeta `pdfs/`

**"Database not found"** → Primero ejecutá `parse_wara.py`

**El dashboard no carga** → Asegurate de que `server_wara.py` esté corriendo en la Terminal

**Un día aparece duplicado** → El sistema lo previene automáticamente. Si querés re-importar un día, borrá la fila correspondiente en `wara.db` con cualquier cliente SQLite (como DB Browser for SQLite, gratuito).
