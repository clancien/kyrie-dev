---
name: java-legacy-maven
description: Trabajar en sistemas Java legacy con Maven, empaquetado WAR, JSP, Struts, Spring MVC antiguo, app servers tradicionales o estructuras monolíticas heredadas. Usar cuando Codex deba corregir bugs, agregar cambios mínimos, investigar flujos Action/Controller-Service-DAO-View, mantener compatibilidad con Java 6/7/8 o evitar regresiones en aplicaciones Java heredadas.
---

# Java Legacy Maven

## Objetivo
Aplicar cambios mínimos y compatibles, reduciendo riesgo de regresión en sistemas Java heredados.

## Checklist de inicio
- Revisar `AGENTS.md`, documentación local y restricciones de compatibilidad.
- Confirmar versión de Java, Maven, app server y formato de despliegue.
- Identificar el layout real del repo: `src/`, `WebContent/`, `src/main/webapp/`, `resources/`, módulos Maven.
- Ubicar configuración relevante: `pom.xml`, `web.xml`, `struts.xml`, Spring XML, `*.properties`.

## Flujo de implementación
1. Trazar el flujo actual desde la entrada hasta la vista o respuesta: Action/Controller -> Service -> DAO -> JSP.
2. Cambiar solo la capa necesaria y preservar contratos existentes.
3. Mantener naming, manejo de errores y patrones históricos del proyecto.
4. Evitar refactors transversales salvo que sean imprescindibles para completar el cambio.
5. Verificar pantallas, endpoints, SQL y flujos afectados con el menor alcance posible.

## Convenciones
- Preservar estilo existente, aunque no sea moderno.
- Agregar comentarios solo para lógica legacy no obvia.
- Mantener compatibilidad con el servidor de aplicaciones y librerías actuales.
- No introducir dependencias, frameworks frontend o cambios de build sin necesidad explícita.

## Comandos base
- Detectar primero si existe wrapper: `./mvnw`.
- Build general: `mvn clean package -DskipTests`.
- Tests: `mvn test`.
- Módulo puntual: `mvn -pl <modulo> -am package`.
- Usar los comandos definidos por el repo cuando existan.
