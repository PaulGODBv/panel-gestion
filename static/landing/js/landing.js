/* Lo único que hace esta página con JavaScript: ir enseñando los bloques
 * según se desplaza, y despegar la barra superior cuando hay contenido debajo.
 *
 * Con IntersectionObserver y no escuchando el scroll: el navegador avisa
 * cuando un elemento entra en pantalla en vez de obligarnos a preguntarlo en
 * cada fotograma, que es lo que hace que una página así vaya a tirones en un
 * teléfono modesto — justo el que va a abrir esto.
 *
 * Las clases que ocultan los bloques las pone este guion, no el HTML. Es
 * deliberado: sin JavaScript no se añaden, no hay nada oculto y la página se
 * lee entera. La animación es un añadido, nunca un requisito para ver el
 * contenido.
 */
(function () {
    "use strict";

    if (!("IntersectionObserver" in window)) return;

    var menosMovimiento = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    /* ---------- Entrada de los bloques ----------
     *
     * Esto si se salta entero con «reducir movimiento»: es lo unico que de
     * verdad mueve algo por la pantalla. La barra de abajo no, porque cambiar
     * de sombra no es movimiento sino un cambio de estado, y quien pide menos
     * animacion no esta pidiendo menos informacion. */

    // `data-mov` elige el gesto. Sin atributo, sube; es lo que vale para el
    // texto corrido, que es la mayoría de la página.
    var GESTOS = {
        derecha: "ld-aparece--derecha",
        izquierda: "ld-aparece--izquierda",
        escala: "ld-aparece--escala"
    };

    var bloques = menosMovimiento ? [] : document.querySelectorAll("[data-aparece]");

    Array.prototype.forEach.call(bloques, function (b) {
        b.classList.add("ld-aparece");
        var gesto = GESTOS[b.getAttribute("data-mov")];
        if (gesto) b.classList.add(gesto);
    });

    var vigia = new IntersectionObserver(function (entradas) {
        entradas.forEach(function (e) {
            if (!e.isIntersecting) return;
            // El retardo escalona los hermanos de una misma rejilla, para que
            // entren en cascada y no todos de golpe.
            var retardo = parseInt(e.target.getAttribute("data-aparece"), 10) || 0;
            setTimeout(function () { e.target.classList.add("ld-visible"); }, retardo);
            // Una vez dentro, se deja de vigilar: la animación es de entrada,
            // no un efecto que se repita cada vez que se sube y se baja. Que
            // los bloques salten cada vez que pasas por delante cansa a la
            // segunda pasada.
            vigia.unobserve(e.target);
        });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });

    Array.prototype.forEach.call(bloques, function (b) { vigia.observe(b); });

    /* ---------- La barra, al despegarse ---------- */

    // Un centinela de un píxel arriba del todo: mientras se ve, la página
    // está sin desplazar. Es la forma de saberlo sin escuchar el scroll, que
    // dispararía decenas de veces por segundo para responder sí o no.
    var barra = document.querySelector(".ld-barra");
    if (!barra) return;

    var centinela = document.createElement("div");
    centinela.setAttribute("aria-hidden", "true");
    centinela.style.cssText = "position:absolute;top:0;left:0;height:1px;width:1px;";
    document.body.insertBefore(centinela, document.body.firstChild);

    new IntersectionObserver(function (entradas) {
        barra.classList.toggle("ld-barra--despegada", !entradas[0].isIntersecting);
    }, { threshold: 0 }).observe(centinela);
})();


/* ---------- El cielo de la portada ----------
 *
 * Va en su propio bloque y no dentro del de arriba porque aquel se corta
 * entero si el navegador no trae IntersectionObserver, y esto no lo necesita.
 *
 * Tres capas con tamanios y velocidades distintas. Esa diferencia de velocidad
 * ES la profundidad: con una sola capa no parece un cielo, parece una pantalla
 * sucia. El movimiento lo lleva CSS; aqui solo se generan las sombras y se
 * atiende al raton.
 */
(function () {
    "use strict";

    var cielo = document.querySelector("[data-cielo]");
    if (!cielo) return;

    var ALTO = 2000;   // el alto del campo; la copia de la hoja va justo a 2000
    var COLOR = "#ffffff";

    /* Menos estrellas en pantalla estrecha. El movimiento sale gratis —es el
     * compositor— pero la PRIMERA pintura de un elemento con doscientas y pico
     * sombras si cuesta, y ahi es donde un telefono flojo se atraganta. */
    var estrecho = window.innerWidth < 768;

    var CAPAS = [
        { cuantas: estrecho ? 70 : 160, tam: 1, vel: 150, opacidad: 0.55 },
        { cuantas: estrecho ? 32 : 70,  tam: 2, vel:  95, opacidad: 0.80 },
        { cuantas: estrecho ? 14 : 26,  tam: 3, vel:  58, opacidad: 1.00 }
    ];

    function sombras(cuantas) {
        var s = [];
        for (var i = 0; i < cuantas; i++) {
            s.push((Math.random() * 100).toFixed(2) + "vw " +
                   (Math.random() * ALTO).toFixed(0) + "px " + COLOR);
        }
        return s.join(",");
    }

    CAPAS.forEach(function (capa, i) {
        var paralaje = document.createElement("div");
        paralaje.className = "ld-cielo__paralaje";
        // La capa de delante se mueve mas con el raton que la del fondo: es lo
        // mismo que mirar por la ventanilla de un bus.
        paralaje.style.setProperty("--ld-prof", (i + 1) * 9);

        var deriva = document.createElement("div");
        deriva.className = "ld-cielo__deriva";
        deriva.style.setProperty("--ld-vel", capa.vel + "s");

        var estrella = document.createElement("div");
        estrella.className = "ld-cielo__estrella";
        estrella.style.setProperty("--ld-tam", capa.tam + "px");
        estrella.style.setProperty("--ld-color", COLOR);
        estrella.style.setProperty("--ld-sombras", sombras(capa.cuantas));
        estrella.style.opacity = capa.opacidad;

        deriva.appendChild(estrella);
        paralaje.appendChild(deriva);
        cielo.appendChild(paralaje);
    });

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    /* El paralaje se aplica una vez por fotograma, no una vez por evento:
     * mousemove dispara decenas de veces por segundo y mover tres capas en
     * cada uno es trabajo tirado. En el telefono no hay raton, asi que alli
     * esto no llega a correr nunca y solo queda la deriva. */
    var portada = cielo.parentElement;
    var x = 0, y = 0, pedido = false;

    portada.addEventListener("mousemove", function (e) {
        var caja = portada.getBoundingClientRect();
        x = (e.clientX - caja.left) / caja.width - 0.5;
        y = (e.clientY - caja.top) / caja.height - 0.5;
        if (pedido) return;
        pedido = true;
        requestAnimationFrame(function () {
            pedido = false;
            var capas = cielo.querySelectorAll(".ld-cielo__paralaje");
            Array.prototype.forEach.call(capas, function (p) {
                var prof = parseFloat(p.style.getPropertyValue("--ld-prof"));
                p.style.transform = "translate3d(" + (-x * prof) + "px," +
                                                     (-y * prof * 0.6) + "px,0)";
            });
        });
    });
})();
