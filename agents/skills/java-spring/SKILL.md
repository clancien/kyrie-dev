---
name: java-spring
description: Trabajar en proyectos Java modernos con Spring Boot, Spring MVC, REST APIs, JPA/Hibernate, seguridad, validación, servicios, jobs o aplicaciones Maven/Gradle. Usar cuando Codex deba implementar endpoints, corregir bugs, ajustar servicios/repositorios, agregar pruebas o mantener separación Controller-Service-Repository en bases Spring.
---

# Java Spring

## Objetivo
Mantener cambios seguros, pequeños y verificables en una base Spring moderna.

## Checklist de inicio
- Revisar `AGENTS.md` y documentación local del proyecto.
- Confirmar versión de Java y Spring Boot desde `pom.xml` o `build.gradle`.
- Identificar módulos y capas afectadas: controller, DTO, service, repository, persistence, security.
- Revisar configuración relevante en `application.yml`, perfiles activos y scripts del repo.

## Flujo de implementación
1. Definir el cambio funcional y su impacto en endpoint, servicio, repositorio y contrato público.
2. Implementar primero la capa de dominio/servicio, luego controlador.
3. Validar entrada en el borde con DTOs, `jakarta.validation` o el patrón existente.
4. Evitar lógica de negocio en controladores.
5. Agregar pruebas unitarias e integración mínimas para el cambio.

## Convenciones
- Código limpio, métodos cortos y nombres explícitos.
- Reusar componentes existentes antes de crear nuevos helpers.
- Evitar hardcode de URLs, secretos, flags de entorno o valores configurables.
- Mantener separación Controller -> Service -> Repository.
- No introducir librerías sin una necesidad clara y localizada.

## Comandos base
- Maven wrapper: `./mvnw test`, `./mvnw clean package`, `./mvnw spring-boot:run`.
- Maven sin wrapper: `mvn test`, `mvn clean package`.
- Gradle wrapper: `./gradlew test`, `./gradlew build`, `./gradlew bootRun`.
- Ejecutar el comando más específico disponible para el módulo afectado.
