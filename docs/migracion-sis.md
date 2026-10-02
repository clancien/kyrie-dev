# Orquestador
Como crear un orquestrador que sea capaz de invocar otros agentes, incluso con modelos distintos para poder completar de forma automatica una migracion completa de tecnologia de un proyecto actual.
El orquestrador tendrá acceso a otros agentes a traves de comandos especificos y deberá ser capaza de esperar cuando los creditos de los agentes se acaben. Tambien debe ser capaz de decidir cual modelo usar segun la complejidad de la tarea.
Cuando el orquestrador requiera decisiones humanas, debe enviar un correo electronico al humano con un enlace para poder leer la consulta y responder. este sistema de comuinicacion debe ser defindio y creado antes de empezar el trabajo real (en la epic 0). este sistema web tambien debe contemplar una forma de visualizar los avances y trabajos realizados por el agente y sub agentes.
nunca se debe hacer push remoto, solamente se debe usar commit local.
Cuando el orquestrador no puede seguir por falta de creditos y debe esperar hasta la proxima ventana, debe enviar un mail al humano para avisarle de todos los trabajos realizados, y esperar hasta la proxima ventana disponible.
El orquestrador debe tener memoria y ser capaz de remotar su trabajo donde mismo lo dejo.
El orquestrador tendra acceso a un modelo exclusivo para poder hacer su trabajo, y tendra acceso a otros modelos de IA para derivar las tareas.
El orquestrador debe tratar de delegar lo mas posible el trabajo, para evitar consumir sus propios tokens. Debe tener un rol de orquestrador.
En la epic 0 se debe trabajar y dejar documentado los pasos de ejecuciones, validaciones, modificaciones, criterios de aceptaciones y ciclos de iteraciones para trabajar.
En la epic 0 se deben definir los agentes que usará el orquestrador y para que usarlos.
La epic 0 será implementada en conjunto con el humano.
El orquestrador debe ser capaz de ejecutar una epic completa sin parar, salvo que este a la espera de 
El orquestrador debe ser capaz de
La epic 0, se debe usar para prepara el trabajo y definir la linea de implementacion completo del proyecto.
El proyecto actual, su codigo fuente y base de datos debe ser tocado, se debe mantener tal cual y el orquestrador debe poder leer el codigo, inspeccionar la base de datos y visualizar la app existente.
El la epic 0 tambien se debe definir la nueva interfaz visual.
En la epic 0 se debe construir el listado exhaustivo de funcionalidades existentes y las modificaciones/mejoras que se realizarán.
se debe contemplar modificaciones de los nombres de las tablas y columnas de la base de datos para sea sean en ingles y que tengan un formato estandar.
se debe configurar ambiente de tipo mock para todos los servicios externos, incluyendo mailpip y un proyecto dedicado.
Para crear sub agentes disponibles en codex, ver la facitibilidad de crear usuarios linux que pertenezcan al mismo grupo "dev" y que tengan los permisos para trabajar, y que cada uno este asociado a una cuenta de chatgpt distinta.
Cada agente codex debe poder usarse con un modelo especifico, especificado por linea de comando.
Se debe poder probar la disponibilidad de un agente codex por linea de comando.
Debe existir archivos claros de reglas de desarrollo, definidos en epic 0, y se pueden ir modificando por el humano durante el desarrollo.
La estructura del orquestrador debe quedar completamente idependiente del proyecto y debe poder ser capaz de aplicarse a otro proyecto, incluso en paralelo.
# Migracion SIS
La migracion del sistema SIS debe ser la siguiente:
- cambio de nombre a Abax, uso de namespaces y packages
- cambio de stack a: single-page app, spring boot sobre undertow, view.js, html y css moderno, api externa documentada, api bff  para servir la app. debe haber investigacion para separacion de responsabilidades de la app y salirse del patron monolitico. mantener base de datos postgres. storage de archivos tipo , con cache local para evitar sobre costo. debe ser arquitectura HA. debe tener una base de datos central para cuentas de clientes ( administracion interna), otra para tablas maestras, y una mas por cada cliente. debe tener enfoque en la seguridad y seguir la nueva reglamentacion de datos de chile (y ojala de europa). debe ser un sitio multi-idioma. 
- mejoras futuras para tomar en cuenta durante la implementacion inicial: sistema de ficha clinica unica para paciente, comuncaicones  entre distintas instancias del abax para poder intercambiar datos de paciente y ordenes medicas, autorizaciones de compartir ficha para paciente, modulo de contabilidad con facturacion electronica, modulo de marketing y mailing (usando un proveedor externo para el envio de mail, whatsapp, u otros), integracion de la IA en toda la app.
