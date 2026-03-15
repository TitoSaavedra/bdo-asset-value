# Black Desert Asset Tracker

![Black Desert Asset Tracker](https://img.shields.io/badge/Black%20Desert%20Online-Asset%20Tracker-blue?style=for-the-badge&logo=game&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135.1-green?style=flat-square&logo=fastapi)
![Tesseract OCR](https://img.shields.io/badge/Tesseract-OCR-orange?style=flat-square)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-yellow?style=flat-square&logo=javascript)

> *Un poderoso sistema de seguimiento de activos para Black Desert Online que combina visión computacional avanzada con una interfaz web intuitiva.*

## 🌟 Visión General

**Black Desert Asset Tracker** es una herramienta automatizada diseñada para jugadores de Black Desert Online que desean mantener un registro preciso y en tiempo real de sus activos financieros. Utilizando técnicas avanzadas de OCR (Reconocimiento Óptico de Caracteres) y procesamiento de imágenes, la aplicación captura automáticamente los valores de plata en el mercado, inventario y almacenes, proporcionando análisis históricos y visualizaciones interactivas.

### ✨ Características Principales

- **OCR Automático**: Detección precisa de valores numéricos en capturas de pantalla del juego
- **Interfaz Web Moderna**: Dashboard interactivo con gráficos en tiempo real
- **Soporte Multi-Almacén**: Seguimiento de múltiples almacenes y tipos de almacenamiento
- **Análisis Histórico**: Tendencias y gráficos de evolución de activos
- **API RESTful**: Backend robusto construido con FastAPI
- **Hotkeys Integradas**: Captura instantánea con atajos de teclado
- **Procesamiento de Imágenes Avanzado**: Múltiples algoritmos de preprocesamiento para máxima precisión OCR

## 🏗️ Arquitectura Técnica

### Backend (Python/FastAPI)

El backend está estructurado en módulos especializados:

- **`app/main.py`**: Punto de entrada FastAPI con endpoints REST
- **`app/service.py`**: Lógica de negocio y gestión de datos
- **`app/models.py`**: Modelos de datos Pydantic
- **`app/storage.py`**: Persistencia de datos (JSON local actualmente, preparado para MongoDB)
- **`app/database.py`**: Cliente MongoDB para futuras migraciones
- **`app/hotkeys.py`**: Sistema de capturas por teclado
- **`app/config.py`**: Configuración centralizada

### OCR Engine

El motor de OCR utiliza Tesseract con procesamiento de imágenes personalizado:

- **`app/ocr/reader.py`**: Lógica principal de reconocimiento de texto
- **`app/ocr/image.py`**: Algoritmos de preprocesamiento de imágenes (bright_text, warm_text, cream_to_bw)
- **`app/ocr/capture.py`**: Captura de pantalla y recorte de regiones
- **`app/ocr/config/`**: Configuraciones de regiones y calibración
- **`app/ocr/utils.py`**: Utilidades de procesamiento y depuración

**Técnicas OCR Avanzadas:**
- Configuración PSM 7 para texto uniforme
- Whitelist de caracteres numéricos
- Múltiples métodos de preprocesamiento (brillo, temperatura de color, binarización)
- Limpieza regex para extracción de dígitos
- Sistema de fallback para mayor robustez

### Frontend (JavaScript Modular)

La interfaz web utiliza una arquitectura modular moderna:

- **`frontend/js/main.js`**: Controlador principal y estado de la aplicación
- **`frontend/js/api.js`**: Cliente API para comunicación con backend
- **`frontend/js/ui-manager.js`**: Gestión de interfaces y navegación
- **`frontend/js/chart-engine.js`**: Renderizado de gráficos con Chart.js
- **`frontend/js/utils.js`**: Utilidades compartidas (formateo de moneda, fechas)

**Características del Frontend:**
- Arquitectura basada en módulos ES6
- Estado centralizado y renderizado reactivo
- Componentes reutilizables
- API asíncrona con manejo de errores
- Visualizaciones interactivas de datos

## � Almacenamiento de Datos

### Almacenamiento Actual (Local JSON)
Actualmente, la aplicación utiliza **almacenamiento local basado en JSON** para simplicidad y portabilidad:

- **Archivo**: `data/asset_history.json`
- **Ventajas**: No requiere configuración adicional, portable, fácil de backup
- **Limitaciones**: Lectura/escritura del archivo completo, no óptimo para grandes volúmenes

### Preparación para MongoDB (Futuro)
El código está preparado para migrar a **MongoDB** cuando sea necesario:

- **Cliente**: Motor (async MongoDB driver)
- **Colecciones**: `records`, `warehouse_snapshots`, `settings`
- **Migración**: Script `migrate_to_mongodb.py` incluido
- **Configuración**: Variables de entorno `MONGODB_URL` y `DATABASE_NAME`

Para migrar a MongoDB más adelante:
1. Instalar MongoDB (local o cloud)
2. Ejecutar `python migrate_to_mongodb.py`
3. Cambiar `storage = JSONStorage()` por `storage = MongoDBStorage()` en `app/storage.py`

## �🚀 Instalación y Configuración

### Prerrequisitos

- **Python 3.8+**
- **Tesseract OCR 5.0+**
- **Windows 10/11** (soporte nativo para capturas de pantalla)

### 1. Instalar Tesseract OCR

> ⚠️ **IMPORTANTE**: Tesseract OCR es **requerido** para la funcionalidad de reconocimiento de texto. Sin él, la aplicación no podrá detectar valores de plata en las capturas de pantalla.

Descarga e instala Tesseract desde el [repositorio oficial de GitHub](https://github.com/UB-Mannheim/tesseract/wiki):

```bash
# Para Windows, descarga el instalador desde:
# https://github.com/UB-Mannheim/tesseract/wiki
```

Asegúrate de que `tesseract.exe` esté en el PATH del sistema.

### 2. Configurar Entorno Python

```bash
# Clonar o descargar el proyecto
cd bdo-asset-value

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Verificar Instalación

```bash
# Verificar Python
python --version

# Verificar Tesseract
tesseract --version

# Verificar dependencias
python -c "import pytesseract, cv2, fastapi; print('Todas las dependencias instaladas correctamente')"
```

## 🎮 Uso

### Inicio Rápido

```bash
# Ejecutar la aplicación
python run.py
```

La aplicación iniciará:
- Servidor web en `http://127.0.0.1:8000`
- Sistema de hotkeys para capturas automáticas

### Hotkeys Disponibles

- **F9**: Capturar inventario
- **F10**: Capturar almacén
- **F11**: Capturar valor de mercado

### Interfaz Web

1. Abre `http://127.0.0.1:8000` en tu navegador
2. Navega entre las pestañas: Dashboard, Historial, Configuración
3. Visualiza gráficos de tendencias de activos
4. Agrega registros manuales si es necesario

### Calibración OCR

Para máxima precisión, calibra las regiones de captura:

1. Ejecuta `python dev.py` para modo desarrollador
2. Ajusta las coordenadas en `app/ocr/config/regions.py`
3. Prueba capturas en diferentes resoluciones de pantalla

## 📊 API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Interfaz web principal |
| GET | `/api/dashboard` | Datos del dashboard |
| POST | `/api/manual-record` | Registro manual de activos |
| POST | `/api/ocr/storage` | Captura OCR de almacén |
| POST | `/api/ocr/inventory` | Captura OCR de inventario |
| POST | `/api/preorders` | Registro de preorders |

## 🔧 Desarrollo

### Estructura del Proyecto

```
bdo-asset-value/
├── app/                    # Backend Python
│   ├── ocr/               # Motor OCR
│   ├── logs/              # Sistema de logging
│   └── *.py               # Módulos principales
├── frontend/              # Interfaz web
│   ├── js/                # JavaScript modular
│   ├── css/               # Estilos
│   └── index.html         # HTML principal
├── data/                  # Datos persistentes
├── requirements.txt       # Dependencias Python
├── run.py                 # Punto de entrada
├── dev.py                 # Modo desarrollador
└── migrate_to_mongodb.py  # Script de migración a MongoDB
```

### Modo Desarrollador

```bash
python dev.py
```

Inicia el servidor con recarga automática para desarrollo.

## � Logging y Depuración

### Configuración de Logs

La aplicación utiliza un sistema de logging dual:

- **Archivo**: `app/logs/bdo_asset_YYYYMMDD.log` - Todos los logs (DEBUG y superiores)
- **Consola**: Muestra todos los logs del OCR y operaciones principales

### Niveles de Logging

```bash
# Mostrar todos los logs (por defecto)
python run.py

# Solo logs INFO y superiores
LOG_LEVEL=INFO python run.py

# Solo logs WARNING y superiores
LOG_LEVEL=WARNING python run.py
```

### Logs del OCR

Todos los logs del OCR se muestran en consola para facilitar la depuración:

- `DEBUG`: Procesamiento detallado de imágenes y texto OCR
- `INFO`: Resultados exitosos de detección de valores
- `WARNING`: Capturas fallidas guardadas para análisis

### Ejemplo de Output en Consola

```
2026-03-15 15:16:11 | DEBUG | reader | read_silver_value | Iniciando lectura de silver con OCR
2026-03-15 15:16:11 | DEBUG | reader | read_silver_value | Imagen procesada con bright_text
2026-03-15 15:16:11 | DEBUG | reader | read_silver_value | OCR resultado primary: 1,234,567
2026-03-15 15:16:11 | INFO | reader | read_silver_value | Silver detectado (modo primary): 1234567
```

## �🚀 Futuras Mejoras

### Detección Automática de Precios de Mercado
- **Integración con APIs de BDO**: Sincronización automática con precios del mercado del juego
- **Análisis Predictivo**: Algoritmos de machine learning para predicción de tendencias
- **Alertas en Tiempo Real**: Notificaciones cuando los precios alcancen umbrales específicos

### Mejoras en OCR
- **IA Avanzada**: Implementación de modelos de visión computacional (CNN) para mayor precisión
- **Soporte Multi-Idioma**: Reconocimiento de texto en múltiples idiomas del juego
- **Detección de Objetos**: Identificación automática de items y cantidades

### Características de la Interfaz
- **Modo Oscuro**: Tema adaptativo para sesiones prolongadas
- **PWA Support**: Instalación como aplicación web progresiva
- **Sincronización en la Nube**: Backup y sincronización de datos entre dispositivos

### Expansión del Sistema
- **Análisis de Portafolio**: Métricas avanzadas de rendimiento de inversiones
- **Integración con Discord**: Webhooks para compartir estadísticas en comunidades
- **Soporte Multi-Plataforma**: Versiones para macOS y Linux

## 🤝 Contribución

¡Las contribuciones son bienvenidas! Para contribuir:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Guías de Contribución

- Sigue PEP 8 para código Python
- Usa ESLint para JavaScript
- Documenta nuevas funciones y cambios
- Agrega tests para funcionalidades críticas

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## ⚠️ Descargo de Responsabilidad

Esta herramienta es para uso personal y educativo únicamente. No está afiliada con Pearl Abyss ni Black Desert Online. El uso de herramientas de automatización puede violar los términos de servicio del juego - úsala bajo tu propio riesgo.

## 🙏 Agradecimientos

- Comunidad de Black Desert Online por la inspiración
- Desarrolladores de Tesseract OCR
- Equipo de FastAPI por el framework excepcional
- Contribuidores de bibliotecas open-source utilizadas

---

**Desarrollado con ❤️ para la comunidad de Black Desert Online**
