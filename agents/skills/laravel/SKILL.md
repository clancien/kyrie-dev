---
name: laravel
description: Trabajar en proyectos Laravel con PHP, Blade, Livewire, Eloquent, colas, jobs, APIs REST, migraciones, seeders, policies o validación de requests. Usar cuando Codex deba implementar cambios funcionales, corregir bugs, ajustar rutas/controladores/modelos/vistas, tocar base de datos versionada o probar flujos Laravel respetando convenciones del framework.
---

# Laravel

## Objetivo
Implementar cambios funcionales respetando convenciones Laravel y trazabilidad de datos.

## Checklist de inicio
- Revisar `AGENTS.md`, documentación local y forma de ejecución del proyecto.
- Identificar versión de PHP/Laravel desde `composer.json`.
- Confirmar si se usa Docker, Sail, contenedores propios o PHP local.
- Revisar rutas, middleware y estructura relevante: `routes/`, `app/Http`, `app/Models`, `resources/views`, `database/`.

## Flujo de implementación
1. Definir el cambio en rutas, controlador, request validation, modelo y vista/API.
2. Llevar reglas de negocio a servicios o modelos cuando corresponda.
3. Aplicar validaciones en FormRequest o validadores explícitos.
4. Crear/ajustar migraciones y seeders si cambia modelo de datos.
5. Probar endpoints, pantallas, jobs o comandos afectados.

## Convenciones
- Mantener controladores ligeros.
- Usar Eloquent scopes/relations antes de duplicar queries.
- No mezclar lógica de negocio compleja en Blade.
- Usar `.env` para configuración sensible.
- Mantener cambios de base de datos versionados en migraciones.
- No ejecutar cambios de schema manuales fuera del flujo acordado del proyecto.

## Comandos base
- Dependencias: `composer install`.
- Migraciones: `php artisan migrate`.
- Tests: `php artisan test`.
- Limpieza cache: `php artisan optimize:clear`.
- En Docker, ejecutar los equivalentes definidos por `docker compose`, Sail o scripts locales.
