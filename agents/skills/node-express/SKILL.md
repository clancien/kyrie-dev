---
name: node-express
description: Trabajar en proyectos Node.js con Express para APIs, servicios backend, SSR liviano, middlewares, validación, autenticación, persistencia, manejo de errores y pruebas. Usar cuando Codex deba implementar endpoints, corregir rutas, ajustar middleware, mantener contratos HTTP, revisar package scripts o agregar validaciones y tests en aplicaciones Express.
---

# Node Express

## Objetivo
Entregar cambios backend robustos con validación, manejo de errores y pruebas mínimas.

## Checklist de inicio
- Revisar `AGENTS.md` y estructura del proyecto.
- Confirmar runtime desde `package.json` (`engines`, scripts, dependencias).
- Identificar middlewares globales (auth, logger, error handler).
- Confirmar si el proyecto usa CommonJS, ESM, TypeScript o JavaScript plano.

## Flujo de implementación
1. Definir contrato del endpoint (input, output, códigos HTTP).
2. Implementar validación en el borde con middleware, schema o patrón existente.
3. Mantener lógica de negocio fuera de rutas.
4. Centralizar errores en middleware de error.
5. Probar rutas críticas y casos de error.

## Convenciones
- Mantener módulos pequeños y cohesionados.
- Evitar estado global mutable.
- Manejar async/await con try/catch o wrapper consistente.
- Validar payloads y sanitizar entradas.
- No filtrar errores internos sensibles al cliente.
- No acoplar rutas directamente a persistencia cuando ya exista capa de servicio.

## Comandos base
- Instalar según lockfile: `npm ci` o `npm install`.
- Desarrollo: `npm run dev`.
- Tests: `npm test`.
- Lint: `npm run lint`.
- Typecheck, si existe: `npm run typecheck`.
