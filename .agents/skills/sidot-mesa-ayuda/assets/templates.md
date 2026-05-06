# Plantillas Mesa de Ayuda SIDOT

## 1) Rechazo por alcance (usuario no existe o deshabilitado)

> {{SALUDO}},
>
> No es posible ayudarle con su solicitud dado que no está dentro de nuestras capacidades. Le recomendamos contactarse con el equipo que administra la plataforma SIDOT, quienes podrán orientarlo con su requerimiento:
>
> - Paulina Acuña (pacuna@minsal.cl)
> - Jaime Muñoz (jaime.munoz@minsal.cl)
> - Carolina Oshiro (carolina.oshiro@minsal.cl)
>
> Atte,
>
> Equipo Mesa de Ayuda SIDOT
>
> /label ~"Estado: Cerrado"
>
> /close

## 2) Solicitud incompleta

> {{SALUDO}},
>
> No es posible proceder con su solicitud debido a que no se cuenta con la información mínima requerida a saber:
>
> - Nombre completo
> - RUT
> - Institución en la que se desempeña
> - Correo electrónico de uso exclusivo ( no se aceptan correos grupales )
> - Fecha de nacimiento
>
> La presente solicitud será cerrada y deberá enviar un correo con los datos solicitados, favor **NO** responder sobre esta misma cadena y generar un nuevo correo.
>
> Atte,
>
> Equipo Mesa de Ayuda SIDOT
>
> /label ~"Estado: Cerrado"
>
> /close

## 3) En proceso

> {{SALUDO}},
>
> Su solicitud está siendo tramitada, se ha solicitado la autorización al equipo que administra la plataforma SIDOT, teniendo su aprobación procederemos a generar una nueva clave y se la enviaremos por este mismo medio.
>
> Tenga en cuenta que el proceso puede demorarse hasta 24hs.
>
> Atte,
>
> Equipo Mesa de Ayuda SIDOT
>
> /label ~"Estado: En proceso"
>
> /status "In progress"

## 4) Correo a administradores SIDOT

Asunto: Verificación de datos para brindar nueva clave de acceso SIDOT

Cuerpo:

> Estimad@s
>
> Favor su ayuda para validar los datos adjuntos para poder proceder con el reinicio de clave.
>
> - Nombre completo:
> - Institución:
> - RUT:
> - Email:
> - Fecha de nacimiento:
> - Link usuario SIDOT:

Destinatarios:

- Paulina Acuña ( pacuna@minsal.cl )
- Jaime Muñoz ( jaime.munoz@minsal.cl )
- Carolina Oshiro ( carolina.oshiro@minsal.cl )
- Trasplante ( trasplante.digera@minsal.cl )

## 5) Entrega de clave temporal y cierre

> {{SALUDO}},
>
> A continuación su nueva clave de acceso temporal, se recomienda cambiar la misma ni bien logre tener acceso a la plataforma.
>
> {{CLAVE_TEMPORAL_20}}
>
> Atte,
>
> Equipo Mesa de Ayuda SIDOT
>
> /label ~"Estado: Cerrado"
>
> /close
