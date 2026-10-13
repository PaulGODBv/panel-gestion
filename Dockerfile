# Imagen del panel. Sirve igual en Azure Container Apps, Render, Railway o Fly:
# lo unico que da por supuesto es que el servicio le pasa un puerto en $PORT y
# termina el TLS por delante.
#
# `slim` y no `alpine`: alpine usa musl en vez de glibc, y entonces las ruedas
# precompiladas de psycopg y Pillow no valen y hay que compilarlas, con su
# compilador y sus cabeceras dentro de la imagen. Se ahorran megas y se pagan
# en minutos de construccion y en fallos raros.
FROM python:3.13-slim

# No escribir .pyc —la capa es de solo lectura y no se reaprovechan— y no
# almacenar la salida, para que los registros del servicio salgan en el momento
# y no cuando se llene un buffer.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Las dependencias en su propia capa: mientras requirements.txt no cambie,
# reconstruir tras tocar el codigo no vuelve a bajarlas.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Los estaticos se recogen al construir, no al arrancar: es trabajo que no
# depende de la base ni de los secretos y no tiene por que repetirse en cada
# despliegue ni retrasar el primer arranque.
#
# Hacen falta valores para que `collectstatic` pueda importar los ajustes, pero
# ninguno llega a la imagen: son de usar y tirar dentro de este RUN. Los de
# verdad los pone el servicio como variables de entorno.
RUN DJANGO_DEBUG=False \
    DJANGO_SECRET_KEY=solo-para-construir-no-se-usa-en-ejecucion \
    DJANGO_ALLOWED_HOSTS=localhost \
    RETA2_API_KEY=solo-para-construir \
    python manage.py collectstatic --noinput

# Sin esto el proceso corre como root dentro del contenedor: si alguien
# aprovecha un fallo de la aplicacion, lo hace con todos los permisos.
RUN useradd --create-home --uid 10001 panel && chown -R panel /app
USER panel

EXPOSE 8000

# `$PORT` lo pone el servicio; 8000 es el valor para correrlo a mano.
#
# Dos trabajadores y dos hilos: el piloto son veinte estudiantes sincronizando
# de vez en cuando, no trafico sostenido. Subirlo solo gastaria memoria.
#
# El tiempo de espera largo es por `collectstatic` de las imagenes de contexto
# y por la primera consulta contra un Postgres gestionado recien despertado.
CMD ["sh", "-c", "python manage.py migrate --noinput && exec gunicorn reta2panel.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --threads 2 --timeout 60 --access-logfile - --error-logfile -"]
