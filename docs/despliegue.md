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
az policy assignment list \
  --query "[?displayName=='Allowed resource deployment regions'].parameters.listOfAllowedLocations.value" \
  -o json
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

## 3. Registrar los proveedores

Una suscripción nueva no tiene habilitados los servicios que va a usar, y el
error no lo dice de forma útil: `MissingSubscriptionRegistration`. Se registran
una vez y de golpe, antes de crear nada:

```bash
for n in Microsoft.App Microsoft.OperationalInsights Microsoft.DBforPostgreSQL Microsoft.ContainerRegistry; do
  az provider register --namespace $n --wait
done
```

En esta suscripción, `Microsoft.App` y `Microsoft.OperationalInsights` ya venían
registrados —los activó el primer intento de crear el entorno—, pero
`Microsoft.DBforPostgreSQL` y `Microsoft.ContainerRegistry` no. El de Postgres
hizo fallar la creación del servidor; el del registro habría hecho fallar el
despliegue más adelante, así que conviene registrarlos los cuatro a la vez y no
descubrirlos de uno en uno.

Comprobar:

```bash
az provider show --namespace Microsoft.DBforPostgreSQL --query registrationState -o tsv
```

> **El aviso de «Paid Tier» no significa que los créditos no se apliquen.** Solo
> dice que ese SKU no está entre los gratuitos para siempre. El saldo de Azure
> for Students es prepago y paga exactamente este tipo de recurso: se ve el
> saldo bajar, no un cobro a una tarjeta.
>
> Son unos 12–15 USD al mes de cómputo más 3–4 de almacenamiento. **El servidor
> se puede parar** hasta siete días seguidos y mientras no consume cómputo:
>
> ```bash
> az postgres flexible-server stop --resource-group reta2 --name reta2-db
> ```

> **Sobre la contraseña del servidor.** La eliges tú en el momento de crearlo, y
> Azure no la vuelve a enseñar. Genérala al azar y guárdala antes de pegarla:
>
> ```bash
> python -c "import secrets; print(secrets.token_urlsafe(24))"
> ```
>
> No la escribas en un chat, en un commit ni en una captura. Si se te escapa,
> cámbiala: `az postgres flexible-server update --resource-group reta2 --name
> reta2-db --admin-password "LA-NUEVA"`.

## 4. Los recursos

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
  --resource-group reta2 --server-name reta2-db --name reta2panel
```

**Ojo con las banderas de esta familia de comandos**, que no siguen el patrón del
resto de la CLI y dan un error que no ayuda:

| Comando | El servidor | La cosa creada |
| --- | --- | --- |
| `flexible-server create` | `--name` | — |
| `flexible-server db create` | `--server-name` | `--name`, **no** `--database-name` |
| `flexible-server firewall-rule` | `--server-name` | `--name` |

**Y comprueba el cortafuegos después.** `--public-access 0.0.0.0` debería dejar
una regla que permita conectarse a los servicios de Azure, y aquí **no la dejó**:
el servidor quedó sin ninguna, es decir, incomunicado.

```bash
az postgres flexible-server firewall-rule list \
  --resource-group reta2 --server-name reta2-db -o table
```

Si sale vacío:

```bash
az postgres flexible-server firewall-rule create \
  --resource-group reta2 --server-name reta2-db \
  --name PermitirServiciosDeAzure \
  --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0
```

El rango `0.0.0.0`–`0.0.0.0` **no es «todo internet»**: es el marcador especial
de Azure para «servicios de Azure». Parece justo lo contrario de lo que hace.

`--public-access 0.0.0.0` permite la entrada desde servicios de Azure. **No es
acceso abierto a internet**, pero conviene revisar las reglas del cortafuegos
después y dejar solo lo necesario.

**Tu máquina también necesita su regla**, o el paso 6 no puede cargar los datos:
la regla de arriba deja entrar a los servicios de Azure, no a ti.

```bash
MI_IP=$(curl -s https://api.ipify.org)
az postgres flexible-server firewall-rule create \
  --resource-group reta2 --server-name reta2-db \
  --name equipo-del-autor \
  --start-ip-address $MI_IP --end-ip-address $MI_IP
```

Conviene borrarla cuando se acabe de cargar, porque una IP domestica cambia y
la regla se queda apuntando a quien la herede:

```bash
az postgres flexible-server firewall-rule delete \
  --resource-group reta2 --server-name reta2-db \
  --name equipo-del-autor --yes
```

## 5. La aplicación

```bash
az containerapp env create --name reta2-env --resource-group reta2 --location mexicocentral
```

### Azure for Students no compila en la nube

Lo natural seria `az containerapp up --source .`, que construye la imagen en
Azure a partir del `Dockerfile`. **No funciona en esta suscripcion**:

```
ERROR: (TasksOperationsNotAllowed) ACR Tasks requests for the registry ... are not permitted.
```

ACR Tasks —el servicio que compila dentro de Azure— esta bloqueado en las
suscripciones de estudiante. El intento fallido deja creado el registro, que si
sirve.

**La vuelta: compilar en local y subir la imagen ya hecha.** Hace falta Docker
en la maquina, que para este proyecto ya hacia falta en el paso 1.

```bash
# El nombre del registro lo dejo el intento fallido; si no, crealo:
#   az acr create --resource-group reta2 --name <nombre> --sku Basic --admin-enabled true
az acr list --resource-group reta2 --query "[].name" -o tsv

docker build -t reta2panel:v1 .
docker tag reta2panel:v1 <registro>.azurecr.io/reta2panel:v1
az acr login --name <registro>
docker push <registro>.azurecr.io/reta2panel:v1
```

Y desplegar **desde la imagen**, no desde el codigo:

```bash
az containerapp create \
  --name reta2panel --resource-group reta2 --environment reta2-env \
  --image <registro>.azurecr.io/reta2panel:v1 \
  --registry-server <registro>.azurecr.io \
  --ingress external --target-port 8000
```

Da una direccion del tipo
`reta2panel.<algo>.mexicocentral.azurecontainerapps.io`, **con HTTPS ya puesto**.

> Para cada version nueva: `docker build`, `docker push` con otra etiqueta, y
> `az containerapp update --image <registro>.azurecr.io/reta2panel:v2`. Conviene
> etiquetar con versiones y no con `latest`: con `latest`, volver atras es
> imposible porque no queda rastro de que imagen estaba antes.

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

### Cambiar la configuracion no basta: hay que destruir la réplica

Esto costo una hora y es lo menos evidente de toda la guia.

El entorno que crea `az containerapp env create` en una suscripcion de
estudiante es **express**. Se reconoce porque la revision se llama siempre
`<app>--latest`, conserva su `createdTime` original y rechaza los sufijos:

```
ERROR: (ExpressEnvironmentFeatureNotSupported) 'Revision Suffix' is not supported
```

En un entorno normal, cambiar la plantilla crea una revision nueva y las
replicas se reemplazan. **Aqui no.** Un `az containerapp update` devuelve la
plantilla nueva, `az containerapp show` la confirma, y la replica que esta
corriendo sigue con la vieja. Si esta en `CrashLoopBackOff`, Azure la reinicia
contra si misma indefinidamente: el contador de reinicios sube y nada cambia.

Se comprobo sin lugar a dudas cambiandole el comando de arranque por un `env`
que imprimiera las variables. Dos minutos despues la replica seguia ejecutando
`manage.py migrate`, el comando anterior.

`az containerapp revision restart` contesta `InternalServerError`. Lo que si
funciona es bajar a cero replicas, esperar a que desaparezca, y volver a subir:

```bash
az containerapp update --name reta2panel --resource-group reta2 --min-replicas 0 --max-replicas 1
# esperar hasta que no quede ninguna
az containerapp replica list --name reta2panel --resource-group reta2 -o table

az containerapp update --name reta2panel --resource-group reta2 --min-replicas 1 --max-replicas 1
curl -s -o /dev/null https://<tu-dominio>/   # hace falta: ver abajo
```

**La peticion del final no es opcional.** Al poner cero replicas, Azure anade
una regla de escalado por HTTP que no se puede quitar y que manda sobre el
minimo: la revision se queda en `ScaledToZero` con `minReplicas: 1` puesto, y
no arranca hasta que llega trafico.

Un cambio de **imagen** (`--image`) si reemplaza la replica por su cuenta. Son
los cambios de variables, secretos y comando los que no llegan.

### El error que no se ve: un `secretRef` con un `value` vacio al lado

Si la aplicacion se creo desde el portal web, una variable puede acabar con las
dos cosas puestas:

```json
{ "name": "DJANGO_SECRET_KEY", "secretRef": "django-secret", "value": "" }
```

Gana el `value`. Al contenedor le llega la cadena vacia y Django se para con
«Falta la variable de entorno DJANGO_SECRET_KEY» mientras el portal enseña la
referencia al secreto, que parece correcta. Las variables sanas solo traen
`secretRef`. Se arregla reescribiendo la lista entera:

```bash
az containerapp update --name reta2panel --resource-group reta2 \
  --replace-env-vars \
    DJANGO_DEBUG=False \
    DJANGO_SSL_REDIRECT=True \
    DJANGO_ALLOWED_HOSTS=<tu-dominio> \
    DJANGO_SECRET_KEY=secretref:django-secret \
    RETA2_API_KEY=secretref:api-key \
    DATABASE_URL=secretref:db-url
```

Para comprobar que llegan de verdad, sin sacar ningun valor a los registros:

```bash
# como comando temporal del contenedor
sh -c 'env | cut -d= -f1 | sort; echo "SECRET=${#DJANGO_SECRET_KEY} DBURL=${#DATABASE_URL}"'
```

### Leer los registros sin flujo en vivo

`az containerapp logs show` falla en un entorno express con
`KeyError: 'eventStreamEndpoint'`: no hay flujo. Hay que ir a Log Analytics.

```bash
az extension add --name log-analytics

az containerapp env show --name reta2-env --resource-group reta2 \
  --query properties.appLogsConfiguration.logAnalyticsConfiguration.customerId -o tsv
```

Tres cosas que hacen perder el tiempo:

**La consulta va en una sola linea.** Partida en varias, el CLI de Windows pasa
solo la primera y se ejecuta `ContainerAppConsoleLogs_CL` a secas: devuelve la
tabla entera y parece que el filtro no encuentra nada.

**Las cadenas se entrecomillan con comillas simples.** Las dobles se las come
`cmd` y sale `Failed to resolve column named 'reta2panel'`.

**La columna es `TimeGenerated`.** Y hay un retraso de dos o tres minutos, asi
que una traza recien aparecida puede ser del arranque anterior. Sin filtro de
tiempo es facil diagnosticar un error que ya se habia arreglado.

```bash
az monitor log-analytics query --workspace <customerId> \
  --analytics-query "ContainerAppConsoleLogs_CL | where ContainerAppName_s == 'reta2panel' | where TimeGenerated > ago(10m) | project T=format_datetime(TimeGenerated,'HH:mm:ss'), L=Log_s | order by T asc"
```

## 6. Llevar los datos

Las migraciones las corre el contenedor al arrancar. Los datos hay que
pasarlos, y el procedimiento es el que ya se verificó en local:

```bash
# 1. Desde la máquina de desarrollo, sin DATABASE_URL puesta
PYTHONIOENCODING=utf-8 python manage.py dumpdata \
  --natural-foreign --natural-primary \
  --exclude contenttypes --exclude auth.permission --exclude auth.group \
  --exclude admin.logentry --exclude sessions.session \
  --exclude core.studentreport --exclude core.levelprogressreport \
  --exclude core.visitaguiada \
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

**Los reportes de estudiante tampoco viajan.** En la base de desarrollo habia
55 reportes y 210 de progreso, todos de las pruebas. Cargarlos pondria al
tablero del piloto a enseñar cifras inventadas desde el primer dia, y a quien
lo evalue no habria forma de decirle cual cifra es real. Lo mismo con
`core.visitaguiada`, que guarda que el recorrido guiado ya se hizo: en el panel
nuevo le esconderia el recorrido al primer superadministrador, que es
precisamente quien lo necesita.

Lo que si viaja es el catalogo —competencias, niveles, preguntas, opciones,
imagenes de contexto—, su historial y las cuentas: 716 objetos de los 983 del
volcado completo. Si algun dia hacen falta los de prueba para una demo, estan
en el mismo volcado y se cargan con un `loaddata` mas.

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

## 7. La cuenta y los archivos

```bash
az containerapp exec --name reta2panel --resource-group reta2 \
  --command "python manage.py createsuperuser"
```

Si se cargaron los datos, las cuentas ya están y no hace falta.

### Las imágenes de las preguntas no se servían

Las 23 preguntas con imagen de contexto pedian `/media/question-context/*.webp`
y recibian un **404** en Azure, aunque los 15 ficheros si estaban dentro de la
imagen del contenedor.

La causa: el `static()` del final de `urls.py` solo devuelve rutas con DEBUG
activo, y el comentario que habia alli daba por supuesto «un servidor web o un
CDN por delante». En Container Apps no hay nada por delante —el contenedor es
el servidor—, asi que no las servia nadie. En local nunca se vio porque en
local DEBUG esta puesto.

Arreglado en `wsgi.py`: WhiteNoise, que ya estaba en la cadena para los
estaticos, sirve tambien el directorio de medios con su prefijo. Es el caso
para el que vale, porque son ficheros que vienen en la imagen y no cambian
mientras el proceso vive. Hay prueba de regresion en
`core/tests.py::MediosEnProduccionTest`, que entra por la aplicacion WSGI y no
por el cliente de Django —el cliente pasa por `urls.py` y se saltaria justo la
capa que se quiere comprobar—.

> **El disco del contenedor es efímero.** Una imagen que se suba por el panel
> se sirve hasta el siguiente reinicio y entonces desaparece, sin aviso y
> dejando la pregunta con un hueco. Las que hay aguantan porque vienen dentro
> de la imagen: para añadir una, se añade al repositorio y se reconstruye. Subir
> medios en caliente pide almacenamiento externo (Azure Blob Storage), y es lo
> mismo que hace falta para el APK y el vídeo de aquí abajo.

El **APK firmado** y el **vídeo** van en `media/`, que no viaja en la imagen. Para
el piloto, lo más simple es subirlos a un Azure Storage y servir `MEDIA_URL`
desde ahí. Mientras no estén, la página pública no enseña un botón roto: dice
que la descarga está en preparación.

## 8. Cerrar el círculo con la app Android

Con el dominio funcionando:

1. `ApiConfig` apunta a `https://reta2panel.<sufijo>.eastus.azurecontainerapps.io/api/`.
2. **Quitar `usesCleartextTraffic` del manifiesto.** Es lo que permitía hablar en
   claro con la IP de la LAN; con HTTPS deja de hacer falta y dejarlo puesto
   mantiene abierta la puerta que el despliegue viene a cerrar.
3. Recompilar, **firmar** y subir el APK a la página pública.

Hasta aquí, la cabecera `X-API-Key` viajaba legible por la red local y se podía
capturar con un analizador sin descompilar nada. Esto es lo que lo arregla; rotar
la clave nunca lo arregló.

## 9. Cuando ya sirva bien por HTTPS

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

Debe quedar en **un solo aviso**: el del HSTS en cero, deliberado hasta el paso
9. Con una clave corta de prueba sale un segundo aviso por la `SECRET_KEY`, que
desaparece en cuanto se usa una de verdad. Cualquier otro hay que mirarlo.

## Dónde quedó, 14/10/2026

Lo que está en pie y comprobado contra el servicio, no supuesto:

| | |
| --- | --- |
| Dirección | `https://reta2panel.graymeadow-2656f405.mexicocentral.azurecontainerapps.io` |
| Imagen | `ca41b540ca9aacr.azurecr.io/reta2panel:v2` |
| Base | PostgreSQL 16.15 en `reta2-db.postgres.database.azure.com`, base `reta2panel` |
| Región | México Central |

Comprobado: la raiz responde 200; `/admin/` sirve el inicio de sesion con los
estilos de Unfold; `/api/competences/` devuelve **403 sin clave** y las 5
competencias con ella; las 18 niveles y 111 preguntas estan cargadas; las 15
imagenes de contexto se sirven con el mismo tamaño byte a byte que en local; y
las secuencias de Postgres avanzan —el `INSERT` de prueba tomo el id siguiente
al maximo—.

Y lo que mas importaba: en esta base, creada de cero, el grupo
`Administradores` quedo con **sus 20 permisos y ninguno en inglés**. Era el
fallo que solo se veia contra una base nueva, y esta lo era.

Falta, y no es poco:

1. **El paso 8 entero.** `ApiConfig` sigue apuntando a la IP de la LAN y el
   manifiesto de Android conserva `usesCleartextTraffic`. Hasta que eso se
   cambie, el despliegue no sirve de nada para la app.
2. **El APK firmado y el vídeo**, que van en `media/` y necesitan el
   almacenamiento externo del paso 7.
3. **El paso 9**, el HSTS. Ya se puede: HTTPS sirve bien. Pero es la puerta de
   un solo sentido que se explica ahí, asi que se decide, no se hace de paso.
4. **Borrar la regla del cortafuegos** `equipo-del-autor` cuando no haga falta
   cargar mas datos.
