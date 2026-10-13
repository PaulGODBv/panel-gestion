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
