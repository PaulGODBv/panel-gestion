# Despliegue en Azure

Panel de Reta2 en **Azure Container Apps** con **Postgres gestionado**. Escrito
el 13/10/2026, con la migración a Postgres ya verificada en local.

> **Estado al 13/10/2026: todo lo que no necesita una cuenta de Azure está
> hecho y verificado.** La migración de datos se probó contra un PostgreSQL
> 17.6, y la imagen se construyó y se ejecutó:
>
> | | |
> | --- | --- |
> | Página pública y login | 200 |
> | Estáticos | servidos con huella en el nombre: `landing.54e655664a4b.css` |
> | Compresión y caché | gzip, `max-age` de diez años, `immutable` |
> | Cabeceras de seguridad | `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy`, COOP |
> | API sin clave / con clave | 403 / 200 |
>
> Lo único que queda sin probar es el contenedor **contra Postgres**: se ejecutó
> sin `DATABASE_URL`, así que usó su SQLite de usar y tirar. El camino de
> Postgres se verificó con el mismo código fuera del contenedor, y lo que los
> separa es una variable de entorno.

---

## 1. Antes de nada: construir la imagen

No tiene sentido pelearse con la nube para descubrir que la imagen no compila.
Esto **ya se hizo y funcionó**; queda escrito para repetirlo tras cualquier
cambio. Con Docker Desktop instalado:

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

Responde en `http://localhost:8000` con la página pública. Sin `DATABASE_URL`
usa un SQLite de usar y tirar dentro del contenedor, que para comprobar que
arranca es suficiente — la API contesta `[]` porque esa base está vacía, y eso
es lo correcto.

## 2. Antes de crear nada: en qué regiones te deja

**Azure for Students solo permite cinco regiones.** Lo impone una política de la
suscripción, y si pides otra, el error no dice «región no permitida» de forma
evidente — dice `RequestDisallowedByAzure`. Míralas primero:

```bash
az policy assignment list   --query "[?displayName=='Allowed resource deployment regions'].parameters.listOfAllowedLocations.value" -o json
```

En esta suscripción, el 13/10/2026, eran: `canadacentral`, `brazilsouth`,
`mexicocentral`, `eastus` y `northcentralus`.

**Y una que está permitida puede no tener sitio.** `eastus` está en la lista y
aun así falló con *«There is not enough space on the disk»*. **No es tu disco**:
es como Azure dice que la región no tiene capacidad para ese recurso en ese
momento. `eastus` es la más saturada que tienen.

Se eligió **`mexicocentral`**: de las cinco permitidas es la más cercana a
Bucaramanga, y en una aplicación que sincroniza desde teléfonos cada petición
paga esa distancia.

> **Si un intento falla, limpia antes de repetir.** Cada intento deja detrás un
> *workspace* de Log Analytics creado automáticamente, y un entorno a medias se
> queda en estado `Failed` ocupando el nombre — el siguiente intento entonces
> falla por un motivo distinto y confuso. Aquí quedaron cuatro *workspaces*
> huérfanos y un entorno muerto:
>
> ```bash
> az resource list --resource-group reta2 -o table
> az containerapp env delete --name reta2-env --resource-group reta2 --yes
> az monitor log-analytics workspace delete --resource-group reta2 >   --workspace-name <el-huerfano> --force true --yes
> ```

## 3. Los recursos

Hace falta una suscripción. **Si la Universidad da créditos académicos, úsalos**:
el Postgres gestionado más barato ronda los 15 dólares al mes y el piloto dura
unas semanas.

La región del **grupo de recursos** da igual —solo guarda metadatos—, pero **la
aplicación y la base tienen que compartir región**: separadas, cada consulta
paga el viaje.

```bash
az login
az group create --name reta2 --location mexicocentral

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

## 4. La aplicación

```bash
az containerapp env create --name reta2-env --resource-group reta2 --location mexicocentral

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

## 5. Llevar los datos

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

## 6. La cuenta y los archivos

```bash
az containerapp exec --name reta2panel --resource-group reta2 \
  --command "python manage.py createsuperuser"
```

Si se cargaron los datos, las cuentas ya están y no hace falta.

El **APK firmado** y el **vídeo** van en `media/`, que no viaja en la imagen. Para
el piloto, lo más simple es subirlos a un Azure Storage y servir `MEDIA_URL`
desde ahí. Mientras no estén, la página pública no enseña un botón roto: dice
que la descarga está en preparación.

## 7. Cerrar el círculo con la app Android

Con el dominio funcionando:

1. `ApiConfig` apunta a `https://reta2panel.<sufijo>.eastus.azurecontainerapps.io/api/`.
2. **Quitar `usesCleartextTraffic` del manifiesto.** Es lo que permitía hablar en
   claro con la IP de la LAN; con HTTPS deja de hacer falta y dejarlo puesto
   mantiene abierta la puerta que el despliegue viene a cerrar.
3. Recompilar, **firmar** y subir el APK a la página pública.

Hasta aquí, la cabecera `X-API-Key` viajaba legible por la red local y se podía
capturar con un analizador sin descompilar nada. Esto es lo que lo arregla; rotar
la clave nunca lo arregló.

## 8. Cuando ya sirva bien por HTTPS

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
paso 8— y, si usas una clave corta de prueba, el de la `SECRET_KEY`. Cualquier
otro hay que mirarlo.
