# ITSM AI Automation

Automatizacion e Integracion de IA para plataformas ITSM (Service Desk). Procesa tickets entrantes utilizando modelos de lenguaje locales (Ollama) para clasificarlos, sugerir resoluciones y reducir el tiempo de respuesta operativa.

## Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                     Docker / Host                        │
│                                                          │
│  ┌──────────────┐    ┌──────────────────────────────┐   │
│  │   Redis 7     │    │      Orchestrator             │   │
│  │   (queue)     │◄───│  - Lee tickets de ITSM        │   │
│  └──────────────┘    │  - Clasifica con IA            │   │
│        ▲             │  - Sugiere resolucion          │   │
│        │             │  - Agrega notas al ticket      │   │
│  ┌─────┴──────────┐  └──────────────────────────────┘   │
│  │    Worker RQ    │                                     │
│  │  - Procesamiento│                                     │
│  │    en background│                                     │
│  └────────────────┘                                      │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │            ITSM Connectors                        │   │
│  │  ┌─────────────┐  ┌─────────────┐                │   │
│  │  │ Freshservice │  │   Zendesk   │                │   │
│  │  └─────────────┘  └─────────────┘                │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │            Ollama (LLM local)                     │   │
│  │  Corre en el host o en otro contenedor            │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Estructura del proyecto

```
itsm-ai-automation/
├── src/
│   ├── config/
│   │   └── settings.py          # Configuracion con pydantic-settings desde .env
│   ├── core/
│   │   ├── logger.py            # Logging estructurado (JSON o texto plano)
│   │   └── security.py          # Encriptacion PBKDF2 y validacion de IP
│   ├── models/
│   │   └── ticket.py            # Modelo Ticket con Pydantic v2
│   ├── connectors/
│   │   ├── base.py              # Interface abstracta ITSMConnector
│   │   ├── freshservice.py      # Implementacion Freshservice API v2
│   │   └── zendesk.py           # Implementacion Zendesk API v2
│   ├── ai/
│   │   ├── llm_client.py        # Cliente asincronico para Ollama
│   │   └── prompts.py           # System prompts y templates en espanol
│   ├── services/
│   │   ├── processor.py         # Logica de clasificacion y resolucion con IA
│   │   └── orchestrator.py      # Bucle principal de procesamiento
│   └── workers/
│       └── ticket_worker.py     # Worker RQ para procesamiento en background
├── docker/
│   ├── Dockerfile               # Imagen Python 3.12-slim
│   └── docker-compose.yml       # redis + orchestrator + worker
├── tests/                       # Suite de pruebas con pytest
│   ├── test_ticket.py
│   ├── test_settings.py
│   ├── test_connectors.py
│   ├── test_ai.py
│   └── test_security.py
├── scripts/
│   └── seed_data.py             # Tickets de ejemplo para pruebas
├── .env.example                 # Template de variables de entorno
├── .gitignore
└── pyproject.toml
```

## Requisitos

- Python 3.12 o superior
- Ollama corriendo en el host (o en un contenedor accesible via HTTP)
- Redis (solo si se usan workers RQ)

## Instalacion

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/itsm-ai-automation.git
cd itsm-ai-automation
```

### 2. Configurar variables de entorno

Copiar el archivo de ejemplo y editarlo:

```bash
cp .env.example .env
```

Variables disponibles:

| Variable | Descripcion | Default |
|---|---|---|
| `FRESHSERVICE_DOMAIN` | Subdominio de Freshservice | `""` |
| `FRESHSERVICE_API_KEY` | API Key de Freshservice | `""` |
| `ZENDESK_DOMAIN` | Subdominio de Zendesk | `""` |
| `ZENDESK_EMAIL` | Email asociado al token de Zendesk | `""` |
| `ZENDESK_API_TOKEN` | API Token de Zendesk | `""` |
| `OLLAMA_BASE_URL` | URL base de la API de Ollama | `http://localhost:11434` |
| `OLLAMA_MODEL` | Modelo de Ollama a utilizar | `llama3` |
| `OLLAMA_TIMEOUT` | Timeout en segundos para la API | `120` |
| `REDIS_URL` | URL de conexion a Redis | `redis://localhost:6379/0` |
| `WORKER_QUEUE` | Nombre de la cola RQ | `itsm-tickets` |
| `WORKER_MAX_RETRIES` | Reintentos maximos por ticket | `3` |
| `LOG_LEVEL` | Nivel de logging | `INFO` |
| `LOG_FORMAT` | Formato de logging (`json` o `text`) | `json` |
| `ALLOWED_IPS` | Lista de IPs permitidas separadas por coma | `0.0.0.0/0` |
| `ENCRYPTION_KEY` | Clave para encriptacion de secretos | `""` |

### 3. Instalar dependencias

```bash
pip install .
```

Para instalar tambien las dependencias de desarrollo:

```bash
pip install -e ".[dev]"
```

### 4. Descargar modelo de Ollama

```bash
ollama pull llama3
```

## Uso

### Ejecutar el orquestador (modo loop)

Procesa tickets en un bucle continuo cada 60 segundos:

```bash
python -m src.services.orchestrator
```

O usando el entry point instalado:

```bash
itsm-process
```

### Ejecutar un worker RQ

Procesa tickets encolados en Redis:

```bash
python -m src.workers.ticket_worker
```

O usando el entry point:

```bash
itsm-worker
```

### Procesamiento unico

Para ejecutar un solo ciclo de procesamiento (sin loop), se puede modificar la llamada a `run_once()` en el codigo:

```python
import asyncio
from src.services.orchestrator import Orchestrator

async def main():
    orch = Orchestrator()
    count = await orch.run_once(max_tickets=20)
    print(f"Procesados {count} tickets")
    await orch.shutdown()

asyncio.run(main())
```

## Despliegue con Docker

### Requisitos

- Docker Engine 24+
- Docker Compose v2+

### Construir y ejecutar

```bash
cd docker
docker compose up -d
```

Esto levanta tres servicios:

- **redis**: Cola de mensajes para los workers
- **orchestrator**: Bucle de procesamiento principal
- **worker**: Procesador de tickets en background

Para ver los logs:

```bash
docker compose logs -f orchestrator
```

### Detener

```bash
docker compose down
```

## Pruebas

Ejecutar la suite completa:

```bash
pytest -v
```

Para pruebas con cobertura:

```bash
pip install pytest-cov
pytest --cov=src
```

## Agregar un nuevo conector ITSM

1. Crear `src/connectors/miplataforma.py`
2. Implementar la clase heredando de `ITSMConnector` (ver `base.py`)
3. Implementar los seis metodos abstractos:
   - `get_ticket(ticket_id) -> Ticket | None`
   - `list_tickets(status, priority, limit) -> list[Ticket]`
   - `stream_all(batch_size) -> AsyncIterator[list[Ticket]]`
   - `update_ticket(ticket_id, fields) -> Ticket | None`
   - `add_note(ticket_id, body, public) -> bool`
   - `health_check() -> bool`
4. Agregar las variables de configuracion en `settings.py`
5. Inicializar el conector en `orchestrator.py`

## Seguridad

- Las claves API se almacenan como `SecretStr` de Pydantic, lo que evita su exposicion en logs y representaciones
- Soporte para encriptacion de secretos via PBKDF2 con SHA-256
- Validacion de IP por CIDR para restringir acceso a endpoints
- El archivo `.env` esta excluido de Git mediante `.gitignore`

## Tecnologias

- Python 3.12+
- Pydantic v2 / pydantic-settings (modelado y configuracion)
- httpx (cliente HTTP asincronico)
- RQ + Redis (cola de tareas en background)
- Ollama (inferencia de LLM local)
- pytest (testing)
- Ruff (linter y formateador)
- Docker / Docker Compose (contenedores)
