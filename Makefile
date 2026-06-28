DC := docker-compose
WEB := web
FRONTEND := frontend
HOST_UID := $(shell id -u)
HOST_GID := $(shell id -g)

.PHONY: help build up down restart ps logs web-logs frontend-logs db-logs backend-shell frontend-shell api-health api-test openapi-export frontend-build fix-perms

help:
	@echo "Targets disponibles:"
	@echo "  make build                 -> Construye imagen backend"
	@echo "  make up                    -> Levanta db, backend y frontend"
	@echo "  make down                  -> Baja servicios sin borrar volumenes"
	@echo "  make restart               -> Reinicia todos los servicios"
	@echo "  make ps                    -> Estado de contenedores"
	@echo "  make logs                  -> Logs de todos los servicios"
	@echo "  make web-logs              -> Logs del backend (web)"
	@echo "  make frontend-logs         -> Logs del frontend"
	@echo "  make db-logs               -> Logs de la base de datos"
	@echo "  make backend-shell         -> Shell dentro del backend"
	@echo "  make frontend-shell        -> Shell dentro del frontend"
	@echo "  make api-health            -> Verifica endpoint de salud API"
	@echo "  make api-test              -> Ejecuta pruebas backend (pytest)"
	@echo "  make openapi-export        -> Exporta OpenAPI a contracts/openapi/openapi-v1.json"
	@echo "  make frontend-build        -> Compila frontend"
	@echo "  make fix-perms             -> Repara permisos root en backend/frontend"

build:
	$(DC) build

up:
	$(DC) up -d

down:
	$(DC) down

restart:
	$(DC) down
	$(DC) up -d

ps:
	$(DC) ps

logs:
	$(DC) logs -f

web-logs:
	$(DC) logs -f $(WEB)

frontend-logs:
	$(DC) logs -f $(FRONTEND)

db-logs:
	$(DC) logs -f db

backend-shell:
	$(DC) exec $(WEB) sh

frontend-shell:
	$(DC) exec $(FRONTEND) sh

api-health:
	$(DC) exec $(WEB) python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/api/v1/health').read().decode())"

api-test:
	$(DC) exec $(WEB) python -m pytest -q

openapi-export:
	@mkdir -p contracts/openapi
	$(DC) exec -T $(WEB) python -c "import json, urllib.request; d=json.loads(urllib.request.urlopen('http://localhost:8000/openapi.json').read().decode()); print(json.dumps(d, indent=2, sort_keys=True))" > contracts/openapi/openapi-v1.json
	@echo "Contrato OpenAPI exportado en contracts/openapi/openapi-v1.json"

frontend-build:
	$(DC) run --rm $(FRONTEND) npm run build

fix-perms:
	$(DC) exec --user root $(WEB) sh -c 'chown -R $(HOST_UID):$(HOST_GID) /app'
	$(DC) exec --user root $(FRONTEND) sh -c 'chown -R $(HOST_UID):$(HOST_GID) /app'
