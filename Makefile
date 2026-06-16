DC := docker-compose
WEB := web
HOST_UID := $(shell id -u)
HOST_GID := $(shell id -g)

.PHONY: help build up down restart ps logs web-logs db-logs shell migrate makemigrations createsuperuser collectstatic startapp fix-perms

help:
	@echo "Targets disponibles:"
	@echo "  make build                 -> Construye las imagenes"
	@echo "  make up                    -> Levanta servicios en background"
	@echo "  make down                  -> Baja servicios (sin borrar volumenes)"
	@echo "  make restart               -> Reinicia servicios"
	@echo "  make ps                    -> Estado de contenedores"
	@echo "  make logs                  -> Logs de todos los servicios"
	@echo "  make web-logs              -> Logs del servicio web"
	@echo "  make db-logs               -> Logs del servicio db"
	@echo "  make shell                 -> Shell dentro de web"
	@echo "  make migrate               -> Ejecuta migraciones"
	@echo "  make makemigrations        -> Crea migraciones"
	@echo "  make createsuperuser       -> Crea superusuario"
	@echo "  make collectstatic         -> Ejecuta collectstatic"
	@echo "  make startapp name=miapp   -> Crea una app Django"
	@echo "  make fix-perms             -> Repara permisos root en /app"

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
	$(DC) logs -f web

db-logs:
	$(DC) logs -f db

shell:
	$(DC) exec $(WEB) sh

migrate:
	$(DC) exec $(WEB) python manage.py migrate

makemigrations:
	$(DC) exec $(WEB) python manage.py makemigrations

createsuperuser:
	$(DC) exec $(WEB) python manage.py createsuperuser

collectstatic:
	$(DC) exec $(WEB) python manage.py collectstatic --noinput

startapp:
	@if [ -z "$(name)" ]; then echo "Uso: make startapp name=miapp"; exit 1; fi
	$(DC) exec $(WEB) python manage.py startapp $(name)

fix-perms:
	$(DC) exec --user root $(WEB) sh -c 'find /app -uid 0 -exec chown $(HOST_UID):$(HOST_GID) {} +'