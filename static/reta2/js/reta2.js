/*
 * Animaciones del panel Reta2.
 * ---------------------------------------------------------------------------
 * Tres piezas, inspiradas en los componentes de animate-ui pero escritas en
 * JavaScript plano: el panel es Django + Tailwind precompilado dentro de
 * django-unfold, así que no hay React ni forma de instalar sus componentes.
 *
 *   1. Cifras que cuentan   — los KPI suben desde cero al aparecer.
 *   2. Cambio de tema       — barrido circular desde el botón pulsado.
 *   3. Barra lateral        — entrada escalonada y marca del elemento activo.
 *
 * Todo respeta `prefers-reduced-motion`: con movimiento reducido cada pieza
 * hace su trabajo pero sin animar.
 */
(function () {
    'use strict';

    var sinMovimiento = function () {
        return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    };

    /* ======================================================================
       1. Cifras que cuentan
       ====================================================================== */

    var NUMERO = /^-?\d+(?:[.,]\d+)?$/;
    var DURACION_CIFRA = 900;

    function formatear(valor, decimales) {
        return valor.toLocaleString('es-CO', {
            minimumFractionDigits: decimales,
            maximumFractionDigits: decimales
        });
    }

    function pintar(nodo, texto, unidad) {
        nodo.textContent = texto;
        if (unidad) {
            var span = document.createElement('span');
            span.className = 'rt-kpi__unit';
            span.textContent = unidad;
            nodo.appendChild(document.createTextNode(' '));
            nodo.appendChild(span);
        }
    }

    /**
     * Lleva el contenido de `nodo` de 0 hasta `destino`.
     *
     * @param {HTMLElement} nodo     elemento cuyo texto se sustituye
     * @param {number}      destino  valor final
     * @param {Object}      opciones {decimales, unidad}
     */
    function contarHasta(nodo, destino, opciones) {
        if (!nodo) {
            return;
        }

        opciones = opciones || {};
        var decimales = opciones.decimales || 0;
        var unidad = opciones.unidad || '';

        nodo.classList.add('rt-count');

        if (sinMovimiento() || !Number.isFinite(destino)) {
            pintar(nodo, formatear(destino, decimales), unidad);
            return;
        }

        var inicio = null;

        function paso(marca) {
            if (inicio === null) {
                inicio = marca;
            }

            var avance = Math.min((marca - inicio) / DURACION_CIFRA, 1);
            // easeOutExpo: arranca rápido y frena al final, que es lo que hace
            // legible la cifra justo antes de detenerse.
            var suavizado = avance === 1 ? 1 : 1 - Math.pow(2, -10 * avance);

            pintar(nodo, formatear(destino * suavizado, decimales), unidad);

            if (avance < 1) {
                requestAnimationFrame(paso);
            }
        }

        requestAnimationFrame(paso);
    }

    // Disponible para las plantillas que rellenan los KPI por fetch.
    window.rtCountUp = contarHasta;

    /**
     * Anima los KPI ya renderizados por Django.
     *
     * Solo entran los que son un número puro: un valor como «2h 30m» o un
     * correo se quedaría a medias y se muestran tal cual.
     */
    function animarCifrasServidor() {
        var nodos = document.querySelectorAll('.rt-kpi__value:not(.rt-kpi__value--text)');

        Array.prototype.forEach.call(nodos, function (nodo) {
            if (nodo.querySelector('.rt-skeleton') || nodo.dataset.rtCounted) {
                return;
            }

            var unidad = nodo.querySelector('.rt-kpi__unit');
            var texto = (unidad ? nodo.firstChild && nodo.firstChild.textContent : nodo.textContent) || '';
            texto = texto.trim();

            if (!NUMERO.test(texto)) {
                return;
            }

            var destino = parseFloat(texto.replace(',', '.'));
            var decimales = (texto.split(/[.,]/)[1] || '').length;

            nodo.dataset.rtCounted = '1';
            contarHasta(nodo, destino, {
                decimales: decimales,
                unidad: unidad ? unidad.textContent.trim() : ''
            });
        });
    }

    /* ======================================================================
       2. Cambio de tema con barrido circular
       ====================================================================== */

    var SELECTOR_TEMA = '[x-on\\:click^="switchTheme"]';
    var DURACION_TEMA = 520;
    var dejandoPasar = false;

    function barridoDeTema(evento) {
        var disparador = evento.target.closest(SELECTOR_TEMA);

        if (!disparador || dejandoPasar) {
            return;
        }

        // Sin View Transitions (Firefox, Safari antiguo) o con movimiento
        // reducido, el clic sigue su curso y el tema cambia sin animación.
        if (typeof document.startViewTransition !== 'function' || sinMovimiento()) {
            return;
        }

        evento.preventDefault();
        evento.stopPropagation();

        var rect = disparador.getBoundingClientRect();
        var x = evento.clientX || rect.left + rect.width / 2;
        var y = evento.clientY || rect.top + rect.height / 2;
        var radio = Math.hypot(
            Math.max(x, window.innerWidth - x),
            Math.max(y, window.innerHeight - y)
        );

        var transicion = document.startViewTransition(function () {
            // Se reenvía el clic para que lo atienda Alpine: así el tema y el
            // estado del menú los sigue gestionando Unfold, no este archivo.
            dejandoPasar = true;
            disparador.click();
            dejandoPasar = false;

            // Dos fotogramas: Alpine aplica la clase del tema en su tick.
            return new Promise(function (resolver) {
                requestAnimationFrame(function () {
                    requestAnimationFrame(resolver);
                });
            });
        });

        transicion.ready.then(function () {
            document.documentElement.animate(
                {
                    clipPath: [
                        'circle(0px at ' + x + 'px ' + y + 'px)',
                        'circle(' + radio + 'px at ' + x + 'px ' + y + 'px)'
                    ]
                },
                {
                    duration: DURACION_TEMA,
                    easing: 'cubic-bezier(0.4, 0, 0.2, 1)',
                    pseudoElement: '::view-transition-new(root)'
                }
            );
        }).catch(function () {
            /* Si la transición se cancela el tema ya cambió: no hay nada que hacer. */
        });
    }

    /* ======================================================================
       3. Barra lateral
       ====================================================================== */

    function animarBarraLateral() {
        var lista = document.getElementById('nav-sidebar-apps');

        if (!lista) {
            return;
        }

        // Entrada escalonada: cada elemento entra 40 ms después del anterior.
        if (!sinMovimiento()) {
            var elementos = lista.querySelectorAll('li');
            Array.prototype.forEach.call(elementos, function (elemento, indice) {
                elemento.style.setProperty('--rt-nav-i', Math.min(indice, 14));
            });
            lista.classList.add('rt-nav-anim');
        }

        // El elemento activo lo marca Unfold con .active; la clase propia
        // evita depender de sus utilidades de Tailwind para dibujar la barra.
        var activo = lista.querySelector('a.active');
        if (activo) {
            activo.classList.add('rt-nav-activo');
        }
    }

    /**
     * Aísla la rueda del ratón dentro de la barra lateral.
     *
     * `overscroll-behavior: contain` (en la hoja de estilos) corta el encadenado
     * cuando la barra puede desplazarse y llega a su tope. Cuando la barra cabe
     * entera y no tiene nada que desplazar, el navegador manda la rueda a la
     * página: este guardia cubre ese caso.
     */
    function aislarDesplazamiento() {
        var barra = document.getElementById('nav-sidebar');

        if (!barra) {
            return;
        }

        barra.addEventListener('wheel', function (evento) {
            var desplazable = evento.target.closest('#nav-sidebar-apps');

            if (desplazable && desplazable.scrollHeight > desplazable.clientHeight) {
                return; // la lista tiene recorrido propio: que se desplace
            }

            evento.preventDefault();
        }, { passive: false });
    }

    /* ====================================================================== */

    function iniciar() {
        animarCifrasServidor();
        animarBarraLateral();
        aislarDesplazamiento();
        document.addEventListener('click', barridoDeTema, true);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', iniciar);
    } else {
        iniciar();
    }
}());
