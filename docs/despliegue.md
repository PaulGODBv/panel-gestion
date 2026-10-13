# Despliegue en Azure

Panel de Reta2 en **Azure Container Apps** con **Postgres gestionado**. Escrito
el 13/10/2026, con la migración a Postgres ya verificada en local.

> **Qué está hecho y qué no.** El código está listo: la base sale de
> `DATABASE_URL`, los estáticos los sirve WhiteNoise, la seguridad del
> transporte se activa sola con `DEBUG=False` y hay un `Dockerfile`. La
> migración de los datos se probó de verdad contra un PostgreSQL 17.6.
>
> **Lo que no se ha podido probar aquí: la imagen.** En esta máquina no hay
> Docker, así que el `Dockerfile` está escrito pero **nunca se ha construido**.
> Es lo primero que hay que hacer, y antes de tocar Azure.

---

## 1. Antes de nada: construir la imagen

No tiene sentido pelearse con la nube para descubrir que la imagen no compila.
Con Docker Desktop instalado:

```bash
docker build -t reta2panel .
docker run --rm -p 8000:8000 \
  -e DJANGO_DEBUG=False \
  -e DJANGO_SECRET_KEY=una-clave-larga-de-prueba \
  -e DJANGO_ALLOWED_HOSTS=localhost \
  -e DJANGO_SSL_REDIRECT=False \
  -e RETA2_API_KEY=una-clave-de-prueba \
  reta2panel
```

`DJANGO_SSL_REDIRECT=False` solo para esta prueba: sin él, Django redirige a
`https://localhost`, que no existe, y parece que el contenedor está roto.

Debería responder en `http://localhost:8000` con la página pública. Sin
`DATABASE_URL` usará un SQLite de usar y tirar dentro del contenedor, que para
comprobar que arranca es suficiente.

## 2. Los recursos en Azure

Hace falta una suscripción. **Si la Universidad da créditos académicos, úsalos**:
el Postgres gestionado más barato ronda los 15 dólares al mes y el piloto dura
unas semanas.

```bash
az login
az group create --name reta2 --location eastus

# Postgres gestionado, el más pequeño que hay
az postgres flexible-server create \
  --resource-group reta2 --name reta2-db \
  --tier Burstable --sku-name Standard_B1ms \
  --storage-size 32 --version 16 \
  --admin-user reta2admin --admin-password "LA-QUE-ELIJAS" \
  --public-access 0.0.0.0

az postgres flexible-server db create \
  --resource-group reta2 --server-name reta2-db --database-name reta2panel
```

`--public-access 0.0.0.0` permite la entrada desde servicios de Azure. **No es
acceso abierto a internet**, pero conviene revisar las reglas del cortafuegos
después y dejar solo lo necesario.

## 3. La aplicación

```bash
az containerapp env create --name reta2-env --resource-group reta2 --location eastus

az containerapp up \
  --name reta2panel --resource-group reta2 --environment reta2-env \
  --source . --ingress external --target-port 8000
```

`containerapp up` construye la imagen en Azure a partir del `Dockerfile` y la
despliega. Da una dirección del tipo
`reta2panel.<algo>.eastus.azurecontainerapps.io`, **con HTTPS ya puesto**.

### Las variables

```bash
az containerapp secret set --name reta2panel --resource-group reta2 --secrets \
  django-secret="$(python -c 'import secrets;print(secrets.token_urlsafe(50))')" \
  api-key="$(python -c 'import secrets;print(secrets.token_urlsafe(32))')" \
  db-url="postgres://reta2admin:LA-QUE-ELIJAS@reta2-db.postgres.database.azure.com:5432/reta2panel?sslmode=require"

az containerapp update --name reta2panel --resource-group reta2 \
  --set-env-vars \
    DJANGO_DEBUG=False \
    DJANGO_ALLOWED_HOSTS=reta2panel.<tu-sufijo>.eastus.azurecontainerapps.io \
    DJANGO_SECRET_KEY=secretref:django-secret \
    RETA2_API_KEY=secretref:api-key \
    DATABASE_URL=secretref:db-url
```

**`sslmode=require` no es opcional**: el Postgres de Azure rechaza las
conexiones en claro. La URL lo pasa tal cual al conector.

Las claves van como *secrets* y no como variables normales: una variable de
entorno corriente se ve en el portal y en `az containerapp show`.

**La `RETA2_API_KEY` tiene que ser la misma que el `local.properties` de la
app Android**, o la API rechaza todas sus peticiones.

## 4. Llevar los datos

Las migraciones las corre el contenedor al arrancar. Los datos hay que
pasarlos, y el procedimiento es el que ya se verificó en local:

```bash
# 1. Desde la máquina de desarrollo, sin DATABASE_URL puesta
PYTHONIOENCODING=utf-8 python manage.py dumpdata \
  --natural-foreign --natural-primary \
  --exclude contenttypes --exclude auth.permission --exclude auth.group \
  --exclude admin.logentry --exclude sessions.session \
  --indent 2 > datos.json

# 2. Contra Azure
DATABASE_URL="postgres://...?sslmode=require" python manage.py loaddata datos.json
```

Cuatro detalles que se aprendieron probándolo, y que no son evidentes:

**La salida va por `stdout`, no por `-o`.** En Windows, `-o` escribe con la
codificación de la consola y los acentos salen rotos; el `loaddata` revienta
después con un error de UTF-8 que no dice de dónde viene.

**`--natural-foreign` es obligatorio.** Los permisos se excluyen porque Django
los recrea, pero la pertenencia a grupos se guarda por id. Sin claves naturales
apuntaría a permisos que en la base nueva tienen otro id.

**El grupo `Administradores` se excluye.** Lo crea `post_migrate`, así que es
estado derivado y no dato. Incluirlo chocaría con el que ya existe.

**Comprueba las secuencias después.** Es el fallo clásico de pasar a Postgres:
`loaddata` inserta ids explícitos y, si las secuencias no avanzan, el siguiente
`INSERT` choca con uno que ya existe. En la prueba local quedaron bien, pero se
verifica en diez segundos:

```bash
python manage.py shell -c "from academics.models import Competence; c=Competence.objects.create(name='x',description='x',order=99); print('id', c.pk); c.delete()"
```

Si el id es el siguiente al máximo, está bien. Si da un error de clave
duplicada, hay que reiniciar las secuencias:

```bash
python manage.py sqlsequencereset academics core | python manage.py dbshell
```

## 5. La cuenta y los archivos

```bash
az containerapp exec --name reta2panel --resource-group reta2 \
  --command "python manage.py createsuperuser"
```

Si se cargaron los datos, las cuentas ya están y no hace falta.

El **APK firmado** y el **vídeo** van en `media/`, que no viaja en la imagen. Para
el piloto, lo más simple es subirlos a un Azure Storage y servir `MEDIA_URL`
desde ahí. Mientras no estén, la página pública no enseña un botón roto: dice
que la descarga está en preparación.

## 6. Cerrar el círculo con la app Android

Con el dominio funcionando:

1. `ApiConfig` apunta a `https://reta2panel.<sufijo>.eastus.azurecontainerapps.io/api/`.
2. **Quitar `usesCleartextTraffic` del manifiesto.** Es lo que permitía hablar en
   claro con la IP de la LAN; con HTTPS deja de hacer falta y dejarlo puesto
   mantiene abierta la puerta que el despliegue viene a cerrar.
3. Recompilar, **firmar** y subir el APK a la página pública.

Hasta aquí, la cabecera `X-API-Key` viajaba legible por la red local y se podía
capturar con un analizador sin descompilar nada. Esto es lo que lo arregla; rotar
la clave nunca lo arregló.

## 7. Cuando ya sirva bien por HTTPS

Subir el HSTS, y solo entonces:

```bash
az containerapp update --name reta2panel --resource-group reta2 \
  --set-env-vars DJANGO_HSTS_SECONDS=31536000
```

Empieza en cero a propósito. Le dice al navegador que no vuelva a entrar por
HTTP durante un año, **y no hay forma de deshacerlo desde el servidor**: lo
recuerda el navegador de cada persona. Con un dominio a medio configurar, eso
deja a alguien sin poder entrar y sin que tú puedas arreglarlo.

## Repaso final

```bash
DJANGO_DEBUG=False DJANGO_SECRET_KEY=... DJANGO_ALLOWED_HOSTS=... RETA2_API_KEY=... \
  python manage.py check --deploy
```

Debe quedar en dos avisos y solo dos: el del HSTS en cero —deliberado hasta el
paso 7— y, si usas una clave corta de prueba, el de la `SECRET_KEY`. Cualquier
otro hay que mirarlo.
