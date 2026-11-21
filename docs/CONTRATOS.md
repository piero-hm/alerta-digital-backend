# Contratos de la API — Alerta Digital

Fuente de verdad de las rutas del backend. El frontend Angular (otro repositorio)
consume estos contratos. Cualquier ruta nueva debe agregarse aquí antes de
implementarse.

## Convenciones generales

- Prefijo de la API: `/api/v1`. La única excepción es `/health`.
- Todas las respuestas son JSON (`application/json`).
- Autenticación: `Authorization: Bearer <jwt>` con el token de Supabase Auth.
  El backend valida firma `ES256`, expiración, `audience="authenticated"` e
  `issuer="{SUPABASE_URL}/auth/v1"`.
- Formato único de error:

```json
{ "code": "CODIGO", "detail": "Mensaje legible" }
```

- Códigos de error:

| Código | HTTP | Uso |
|---|---|---|
| `VALIDACION` | 422 | Body, query o path inválido |
| `NO_ENCONTRADO` | 404 | Recurso inexistente |
| `CONFLICTO` | 409 | Recurso duplicado o estado incompatible |
| `NO_AUTENTICADO` | 401 | Token ausente, inválido o expirado |
| `SIN_PERMISO` | 403 | Usuario sin perfil o rol insuficiente |
| `DNI_INVALIDO` | 422 | DNI con formato incorrecto |
| `DNI_NO_ENCONTRADO` | 404 | DNI no existe en el proveedor |
| `SERVICIO_EXTERNO_NO_DISPONIBLE` | 503 | Falla de un proveedor externo |
| `ERROR_INTERNO` | 500 | Error no controlado (sin detalles técnicos) |

- Fechas en ISO 8601 (`YYYY-MM-DD` para fechas, ISO completo con zona para
  timestamps).
- Los endpoints públicos no devuelven datos personales (`usuario_id`, DNI,
  email ni datos de contacto).

## Salud

### GET /health

- **Auth:** no requerida.
- **Base de datos:** no la consulta.
- **Body:** ninguno.
- **Respuesta 200:**

```json
{ "status": "ok" }
```

- **Errores:** ninguno esperado.

## Módulo Aprender

### GET /api/v1/aprender/temas

Lista los temas **publicados** (`publicado = true`).

- **Auth:** no requerida (público).
- **Query params:**
  - `publico_objetivo` (opcional): `todos` | `adulto_mayor` | `joven`.
    Si se envía, devuelve los temas de ese público **más** los de público
    `todos` (contenido general aplica a todos). Sin el parámetro, devuelve
    todos los temas publicados.
- **Body:** ninguno.
- **Respuesta 200:** arreglo de temas ordenado por `id` ascendente.

```json
[
  {
    "id": 1,
    "slug": "phishing-que-es",
    "titulo": "¿Qué es el phishing?",
    "resumen": "Aprende a reconocer mensajes falsos.",
    "publico_objetivo": "todos"
  }
]
```

- **Errores:**
  - `422 VALIDACION` si `publico_objetivo` no es uno de los valores permitidos.
  - `500 ERROR_INTERNO` si falla la base de datos.

### GET /api/v1/aprender/temas/{slug}

Devuelve un tema **publicado** con todos sus bloques ordenados por `orden`.

- **Auth:** no requerida (público).
- **Path params:**
  - `slug` (string, requerido): identificador legible del tema.
- **Body:** ninguno.
- **Respuesta 200:**

```json
{
  "id": 1,
  "slug": "phishing-que-es",
  "titulo": "¿Qué es el phishing?",
  "resumen": "Aprende a reconocer mensajes falsos.",
  "publico_objetivo": "todos",
  "bloques": [
    {
      "id": 10,
      "orden": 1,
      "tipo": "texto",
      "contenido": "El phishing es un intento de engaño...",
      "recurso_url": null
    },
    {
      "id": 11,
      "orden": 2,
      "tipo": "video",
      "contenido": null,
      "recurso_url": "dQw4w9WgXcQ"
    }
  ]
}
```

`tipo` es uno de: `texto`, `imagen`, `video`, `alerta`, `lista`.
Para `video`, `recurso_url` contiene solo el id del video de YouTube.

- **Errores:**
  - `404 NO_ENCONTRADO` si el slug no existe o el tema no está publicado.
  - `500 ERROR_INTERNO` si falla la base de datos.

## Módulo Practicar

### GET /api/v1/practicar/temas/{slug}/preguntas

Devuelve las preguntas **activas** de un tema **publicado**, con sus opciones.
No incluye `es_correcta` ni `explicacion`: la explicación solo se entrega
después de responder.

- **Auth:** no requerida (público).
- **Path params:**
  - `slug` (string, requerido): identificador del tema.
- **Body:** ninguno.
- **Respuesta 200:** arreglo de preguntas ordenado por `id`; las opciones se
  ordenan por `id`.

```json
[
  {
    "id": 1,
    "enunciado": "¿Qué harías si recibes este mensaje?",
    "mensaje_simulado": "Hola, soy tu banco y necesito verificar tus datos...",
    "opciones": [
      { "id": 1, "texto": "No hacer clic y llamar al banco" },
      { "id": 2, "texto": "Ingresar mis datos en el enlace" }
    ]
  }
]
```

- **Errores:**
  - `404 NO_ENCONTRADO` si el tema no existe o no está publicado.
  - `500 ERROR_INTERNO` si falla la base de datos.

### POST /api/v1/practicar/responder

Registra una respuesta del usuario autenticado. **Siempre inserta una fila
nueva** en `respuesta_usuario`; no borra respuestas anteriores.

- **Auth:** requerida (`Authorization: Bearer <jwt>`) y el usuario debe tener
  perfil.
- **Body:**

```json
{ "opcion_id": 2 }
```

- **Respuesta 200:**

```json
{
  "es_correcta": false,
  "explicacion": "Nunca ingreses tus datos desde un enlace recibido por mensaje."
}
```

- **Errores:**
  - `401 NO_AUTENTICADO` si falta el token o es inválido/expirado.
  - `403 SIN_PERMISO` con detalle `"Falta completar el perfil"` si no tiene perfil.
  - `404 NO_ENCONTRADO` si la opción no existe, la pregunta está inactiva o el
    tema no está publicado.
  - `422 VALIDACION` si `opcion_id` no es un entero positivo.
  - `500 ERROR_INTERNO` si falla la base de datos.

### GET /api/v1/practicar/progreso/me

Devuelve el progreso del usuario autenticado usando la vista
`v_progreso_tema`. Solo incluye temas publicados.

- **Auth:** requerida (`Authorization: Bearer <jwt>`) y el usuario debe tener
  perfil.
- **Body:** ninguno.
- **Respuesta 200:** arreglo ordenado por `tema_id`.

```json
[
  {
    "tema_id": 1,
    "slug": "phishing-que-es",
    "titulo": "¿Qué es el phishing?",
    "total_preguntas": 3,
    "correctas": 2,
    "porcentaje": 66.67,
    "completado": false
  }
]
```

`porcentaje` se redondea a 2 decimales. `completado` es `true` cuando
`total_preguntas > 0` y `correctas == total_preguntas`.

- **Errores:**
  - `401 NO_AUTENTICADO` si falta el token o es inválido/expirado.
  - `403 SIN_PERMISO` con detalle `"Falta completar el perfil"` si no tiene perfil.
  - `500 ERROR_INTERNO` si falla la base de datos.

### POST /api/v1/practicar/verificar-enlace

Verifica una URL con Google Safe Browsing y heurísticas básicas (HTTP sin TLS,
IP literal, punycode, acortadores, puertos no habituales, exceso de subdominios
o palabras sospechosas). No guarda nada en la base de datos.

- **Auth:** no requerida (público).
- **Body:**

```json
{ "url": "https://ejemplo.com" }
```

- **Respuesta 200:**

```json
{ "resultado": "seguro" }
```

`resultado` es uno de: `seguro`, `sospechoso`, `peligroso`.

- **Errores:**
  - `422 VALIDACION` si la URL no es válida (solo `http`/`https`, máximo 2048
    caracteres).
  - `503 SERVICIO_EXTERNO_NO_DISPONIBLE` si falta `SAFE_BROWSING_API_KEY` o el
    proveedor falla.
  - `500 ERROR_INTERNO` ante un error inesperado.

## Catálogos (transversal)

### GET /api/v1/catalogos

Devuelve los catálogos necesarios para los formularios del frontend.

- **Auth:** no requerida (público).
- **Body:** ninguno.
- **Respuesta 200:** cada lista ordenada por `nombre`.

```json
{
  "departamentos": [{ "id": 15, "nombre": "Lima" }],
  "tipos_fraude": [{ "id": 1, "nombre": "phishing" }],
  "canales": [{ "id": 1, "nombre": "whatsapp" }]
}
```

- **Errores:**
  - `500 ERROR_INTERNO` si falla la base de datos.

## DNI (transversal)

### GET /api/v1/dni/{numero}

Consulta los datos de una persona por DNI en el proveedor externo
(apisperu.com). El backend valida el formato y cachea los resultados exitosos
en memoria durante 1 hora.

- **Auth:** no requerida (público).
- **Path params:**
  - `numero` (string, requerido): exactamente 8 dígitos numéricos.
- **Body:** ninguno.
- **Respuesta 200:**

```json
{
  "dni": "42948117",
  "nombres": "JOSE WILLIANS",
  "apellido_paterno": "NAVARRO",
  "apellido_materno": "YOVERA"
}
```

`apellido_materno` puede ser `null` si el proveedor no lo devuelve.

- **Errores:**
  - `422 DNI_INVALIDO` si el número no tiene exactamente 8 dígitos.
  - `404 DNI_NO_ENCONTRADO` si el DNI no existe en el proveedor.
  - `503 SERVICIO_EXTERNO_NO_DISPONIBLE` si el proveedor falla, no responde
    o no está configurado.

## Autenticación y perfil (transversal)

### POST /api/v1/auth/perfil

Crea el perfil del usuario autenticado. El backend **vuelve a consultar el DNI**
(no confía en los nombres que envíe el cliente), toma el email del JWT y crea
la fila en `usuario` con `id = sub`, rol `ciudadano` y `acepto_datos_en = now()`.

- **Auth:** requerida (`Authorization: Bearer <jwt>`). El usuario puede no tener
  perfil todavía.
- **Body:**

```json
{
  "dni": "42948117",
  "acepto_datos": true
}
```

- **Respuesta 201:** perfil creado.

```json
{
  "id": "11111111-1111-1111-1111-111111111111",
  "dni": "42948117",
  "nombres": "JOSE WILLIANS",
  "apellido_paterno": "NAVARRO",
  "apellido_materno": "YOVERA",
  "email": "persona@ejemplo.com",
  "rol": "ciudadano",
  "activo": true,
  "acepto_datos_en": "2026-11-19T12:00:00Z",
  "creado_en": "2026-11-19T12:00:00Z"
}
```

- **Errores:**
  - `401 NO_AUTENTICADO` si falta el token o es inválido/expirado.
  - `422 VALIDACION` si el DNI no tiene 8 dígitos, falta `acepto_datos` o es
    `false`.
  - `409 CONFLICTO` si el perfil ya existe o el DNI ya está registrado.
  - `404 DNI_NO_ENCONTRADO` si el DNI no existe en el proveedor.
  - `503 SERVICIO_EXTERNO_NO_DISPONIBLE` si el proveedor de DNI falla.
  - `500 ERROR_INTERNO` si falla la base de datos.

### GET /api/v1/auth/me

Devuelve el perfil del usuario autenticado y el nombre de su rol.

- **Auth:** requerida (`Authorization: Bearer <jwt>`) y el usuario debe tener
  perfil.
- **Body:** ninguno.
- **Respuesta 200:** mismo formato que la respuesta de `POST /api/v1/auth/perfil`.
- **Errores:**
  - `401 NO_AUTENTICADO` si falta el token o es inválido/expirado.
  - `403 SIN_PERMISO` con detalle `"Falta completar el perfil"` si el usuario
    aún no tiene perfil.
  - `500 ERROR_INTERNO` si falla la base de datos.

## Módulo Reportar

### POST /api/v1/reportar

Crea un reporte de estafa con estado inicial `pendiente`.

- **Auth:** requerida (`Authorization: Bearer <jwt>`), perfil completo y rol
  `ciudadano`.
- **Body:**

```json
{
  "tipo_fraude_id": 1,
  "canal_id": 1,
  "departamento_id": 15,
  "descripcion": "Recibí un mensaje falso pidiendo mis datos bancarios.",
  "monto_afectado": 150.00,
  "fecha_incidente": "2026-11-18",
  "evidencia_url": "https://ejemplo.com/captura.png"
}
```

`monto_afectado` es opcional (por defecto `0`). `evidencia_url` es opcional.

- **Respuesta 201:** reporte creado.

```json
{
  "id": 1,
  "tipo_fraude": "phishing",
  "canal": "whatsapp",
  "departamento": "Lima",
  "estado": "pendiente",
  "descripcion": "Recibí un mensaje falso pidiendo mis datos bancarios.",
  "monto_afectado": 150.0,
  "fecha_incidente": "2026-11-18",
  "evidencia_url": "https://ejemplo.com/captura.png",
  "creado_en": "2026-11-19T12:00:00Z"
}
```

- **Errores:**
  - `401 NO_AUTENTICADO` si falta el token o es inválido/expirado.
  - `403 SIN_PERMISO` si no tiene perfil o su rol no es `ciudadano`.
  - `422 VALIDACION` si `monto_afectado < 0`, `fecha_incidente` es futura,
    `descripcion` no tiene entre 20 y 3000 caracteres o algún id de catálogo no
    existe.
  - `500 ERROR_INTERNO` si falla la base de datos.

### GET /api/v1/reportar/mios

Devuelve los reportes del usuario autenticado con su estado, ordenados del más
reciente al más antiguo.

- **Auth:** requerida (`Authorization: Bearer <jwt>`) y perfil completo.
- **Body:** ninguno.
- **Respuesta 200:** arreglo de reportes con el mismo formato de
  `POST /api/v1/reportar`.
- **Errores:**
  - `401 NO_AUTENTICADO` si falta el token o es inválido/expirado.
  - `403 SIN_PERMISO` con detalle `"Falta completar el perfil"` si no tiene perfil.
  - `500 ERROR_INTERNO` si falla la base de datos.

### GET /api/v1/reportar/alertas

Devuelve reportes con estado `validado` de forma **anónima**: no incluye
`usuario_id`, DNI, email ni datos de contacto.

- **Auth:** no requerida (público).
- **Query params:**
  - `pagina` (opcional, por defecto `1`, mínimo `1`).
  - `limite` (opcional, por defecto `20`, entre `1` y `100`).
- **Body:** ninguno.
- **Respuesta 200:**

```json
{
  "total": 42,
  "pagina": 1,
  "limite": 20,
  "alertas": [
    {
      "tipo_fraude": "phishing",
      "canal": "whatsapp",
      "departamento": "Lima",
      "fecha_incidente": "2026-11-18",
      "descripcion": "Recibí un mensaje falso pidiendo mis datos bancarios."
    }
  ]
}
```

- **Errores:**
  - `422 VALIDACION` si `pagina` o `limite` están fuera de rango.
  - `500 ERROR_INTERNO` si falla la base de datos.

## Dashboard (transversal)

Las tres rutas son públicas y usan las vistas `v_top_estafas`,
`v_reportes_departamento` y `v_reportes_mensual`. Solo devuelven datos
agregados.

### GET /api/v1/dashboard/top-estafas

- **Auth:** no requerida.
- **Respuesta 200:** arreglo ordenado de mayor a menor por `total`.

```json
[{ "tipo_fraude": "phishing", "total": 12 }]
```

- **Errores:** `500 ERROR_INTERNO` si falla la base de datos.

### GET /api/v1/dashboard/por-departamento

- **Auth:** no requerida.
- **Respuesta 200:** arreglo ordenado de mayor a menor por `total`.

```json
[{ "departamento": "Lima", "total": 8 }]
```

- **Errores:** `500 ERROR_INTERNO` si falla la base de datos.

### GET /api/v1/dashboard/mensual

- **Auth:** no requerida.
- **Respuesta 200:** arreglo ordenado por mes ascendente.

```json
[
  {
    "mes": "2026-11-01T00:00:00Z",
    "total": 5,
    "monto_afectado": 1250.50
  }
]
```

- **Errores:** `500 ERROR_INTERNO` si falla la base de datos.

## Módulo Admin (moderación y administración)

Todas las rutas de este módulo requieren `Authorization: Bearer <jwt>` y perfil
completo. La moderación de reportes permite los roles `moderador` y `admin`; la
gestión de contenido requiere el rol `admin`.

### GET /api/v1/admin/reportes

Lista todos los reportes, opcionalmente filtrados por estado.

- **Auth:** `moderador` o `admin`.
- **Query params:** `estado` (opcional): `pendiente`, `validado` o `rechazado`.
- **Respuesta 200:** arreglo ordenado del más reciente al más antiguo.

```json
[
  {
    "id": 1,
    "usuario_id": "11111111-1111-1111-1111-111111111111",
    "email": "persona@ejemplo.com",
    "tipo_fraude": "phishing",
    "canal": "whatsapp",
    "departamento": "Lima",
    "descripcion": "Recibí un mensaje falso pidiendo mis datos.",
    "monto_afectado": 150.0,
    "fecha_incidente": "2026-11-18",
    "evidencia_url": null,
    "estado": "pendiente",
    "creado_en": "2026-11-19T12:00:00Z"
  }
]
```

- **Errores:**
  - `401 NO_AUTENTICADO` si falta el token o es inválido/expirado.
  - `403 SIN_PERMISO` si el rol no es `moderador` ni `admin`.
  - `422 VALIDACION` si `estado` no existe en el catálogo.
  - `500 ERROR_INTERNO` si falla la base de datos.

### PATCH /api/v1/admin/reportes/{id}/estado

Modera un reporte pendiente.

- **Auth:** `moderador` o `admin`.
- **Body:** `{ "estado": "validado" }` o `{ "estado": "rechazado" }`.
- **Regla:** solo se permite pasar de `pendiente` a `validado` o `rechazado`.
- **Respuesta 200:** reporte actualizado con el mismo formato del listado.
- **Logging:** se registra con `logging` el id del reporte, el email y uuid del
  moderador, el estado anterior, el nuevo estado y la fecha/hora UTC del cambio.
- **Errores:**
  - `401 NO_AUTENTICADO` si falta el token o es inválido/expirado.
  - `403 SIN_PERMISO` si el rol no es `moderador` ni `admin`.
  - `404 NO_ENCONTRADO` si el reporte no existe.
  - `409 CONFLICTO` si el reporte ya no está en estado `pendiente`.
  - `422 VALIDACION` si el estado solicitado no es `validado` ni `rechazado`.
  - `500 ERROR_INTERNO` si falla la base de datos.

### GET /api/v1/admin/temas

Lista todos los temas, publicados y no publicados.

- **Auth:** `admin`.
- **Respuesta 200:** arreglo de temas ordenado por `id`.

```json
[
  {
    "id": 1,
    "slug": "phishing",
    "titulo": "Phishing",
    "resumen": "Aprende a reconocer mensajes falsos.",
    "publico_objetivo": "todos",
    "publicado": false
  }
]
```

- **Errores:** `401`, `403`, `500`.

### GET /api/v1/admin/temas/{id}

Devuelve un tema con sus bloques y preguntas. Cada pregunta incluye sus
opciones, con `es_correcta` y la explicación de la pregunta.

- **Auth:** `admin`.
- **Respuesta 200:**

```json
{
  "id": 1,
  "slug": "phishing",
  "titulo": "Phishing",
  "resumen": "Aprende a reconocer mensajes falsos.",
  "publico_objetivo": "todos",
  "publicado": false,
  "bloques": [
    {
      "id": 10,
      "tema_id": 1,
      "orden": 1,
      "tipo": "texto",
      "contenido": "Contenido del bloque.",
      "recurso_url": null
    }
  ],
  "preguntas": [
    {
      "id": 20,
      "tema_id": 1,
      "enunciado": "¿Qué haces?",
      "mensaje_simulado": null,
      "explicacion": "No compartas tus datos.",
      "activa": true,
      "opciones": [
        {
          "id": 30,
          "pregunta_id": 20,
          "texto": "Opción A",
          "es_correcta": true
        }
      ]
    }
  ]
}
```

- **Errores:** `401`, `403`, `404`, `500`.

### POST /api/v1/admin/temas

Crea un tema no publicado.

- **Auth:** `admin`.
- **Body:**

```json
{
  "slug": "phishing",
  "titulo": "Phishing",
  "resumen": "Aprende a reconocer mensajes falsos.",
  "publico_objetivo": "todos"
}
```

`publico_objetivo` es `todos`, `adulto_mayor` o `joven`.

- **Respuesta 201:** tema creado con `publicado: false`.
- **Errores:**
  - `401`, `403`.
  - `409 CONFLICTO` si el `slug` ya existe.
  - `422 VALIDACION` si el body es inválido.
  - `500`.

### PATCH /api/v1/admin/temas/{id}

Edita un tema. Todos los campos son opcionales.

- **Auth:** `admin`.
- **Body:** `{ "slug": "...", "titulo": "...", "resumen": "...", "publico_objetivo": "..." }`
- **Respuesta 200:** tema actualizado.
- **Errores:** `401`, `403`, `404`, `409` (slug duplicado), `422`, `500`.

### PATCH /api/v1/admin/temas/{id}/publicacion

Publica o despublica un tema.

- **Auth:** `admin`.
- **Body:** `{ "publicado": true }` o `{ "publicado": false }`.
- **Respuesta 200:** tema actualizado.
- **Errores:** `401`, `403`, `404`, `422`, `500`.

### POST /api/v1/admin/temas/{id}/bloques

Crea un bloque dentro de un tema.

- **Auth:** `admin`.
- **Body:**

```json
{
  "orden": 1,
  "tipo": "texto",
  "contenido": "Contenido del bloque.",
  "recurso_url": null
}
```

`tipo` es `texto`, `imagen`, `video`, `alerta` o `lista`. El `orden` es único
dentro del tema. Para `video`, `recurso_url` guarda el id del video de YouTube.

- **Respuesta 201:** bloque creado.
- **Errores:** `401`, `403`, `404` (tema inexistente), `409` (orden duplicado),
  `422`, `500`.

### PATCH /api/v1/admin/bloques/{id}

Edita un bloque. Todos los campos son opcionales.

- **Auth:** `admin`.
- **Body:** `{ "orden": 2, "tipo": "alerta", "contenido": "...", "recurso_url": null }`
- **Respuesta 200:** bloque actualizado.
- **Errores:** `401`, `403`, `404`, `409` (orden duplicado), `422`, `500`.

### POST /api/v1/admin/temas/{id}/preguntas

Crea una pregunta para un tema.

- **Auth:** `admin`.
- **Body:**

```json
{
  "enunciado": "¿Qué haces?",
  "mensaje_simulado": null,
  "explicacion": "No compartas tus datos.",
  "activa": true
}
```

- **Respuesta 201:** pregunta creada con `opciones: []`.
- **Errores:** `401`, `403`, `404` (tema inexistente), `422`, `500`.

### PATCH /api/v1/admin/preguntas/{id}

Edita una pregunta. Todos los campos son opcionales.

- **Auth:** `admin`.
- **Body:** `{ "enunciado": "...", "mensaje_simulado": "...", "explicacion": "...", "activa": false }`
- **Respuesta 200:** pregunta actualizada con sus opciones.
- **Errores:** `401`, `403`, `404`, `422`, `500`.

### POST /api/v1/admin/preguntas/{id}/opciones

Crea una opción para una pregunta.

- **Auth:** `admin`.
- **Body:** `{ "texto": "Opción A", "es_correcta": true }`
- **Regla:** una pregunta puede tener como máximo una opción correcta.
- **Respuesta 201:** opción creada.
- **Errores:** `401`, `403`, `404` (pregunta inexistente), `409` (ya existe una
  opción correcta), `422`, `500`.

### PATCH /api/v1/admin/opciones/{id}

Edita una opción. Todos los campos son opcionales.

- **Auth:** `admin`.
- **Body:** `{ "texto": "Opción B", "es_correcta": false }`
- **Regla:** una pregunta puede tener como máximo una opción correcta.
- **Respuesta 200:** opción actualizada.
- **Errores:** `401`, `403`, `404`, `409` (ya existe otra opción correcta),
  `422`, `500`.

## Roles

Los roles `moderador` y `admin` se asignan directamente con SQL en la tabla
`usuario`. No existe endpoint para auto-asignarse un rol.

