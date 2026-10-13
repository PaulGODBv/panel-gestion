/* Lo único que hace esta página con JavaScript: ir enseñando los bloques
 * según se desplaza.
 *
 * Con IntersectionObserver y no escuchando el scroll: el navegador avisa
 * cuando un elemento entra en pantalla en vez de obligarnos a preguntarlo en
 * cada fotograma, que es lo que hace que una página así vaya a tirones en un
 * teléfono modesto — justo el que va a abrir esto.
 *
 * La clase `.ld-aparece` la pone este guion, no el HTML. Es deliberado: sin
 * JavaScript no se añade, no hay nada oculto y la página se lee entera. La
 * animación es un añadido, nunca un requisito para ver el contenido.
 */
(function () {
    "use strict";

    var menosMovimiento = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (menosMovimiento.matches) return;

    var bloques = document.querySelectorAll("[data-aparece]");
    if (!bloques.length || !("IntersectionObserver" in window)) return;

    bloques.forEach(function (b) { b.classList.add("ld-aparece"); });

    var vigia = new IntersectionObserver(function (entradas) {
        entradas.forEach(function (e) {
            if (!e.isIntersecting) return;
            // El retardo escalona los hermanos de una misma rejilla, para que
            // entren en cascada y no todos de golpe.
            var retardo = parseInt(e.target.getAttribute("data-aparece"), 10) || 0;
            setTimeout(function () { e.target.classList.add("ld-visible"); }, retardo);
            // Una vez dentro, se deja de vigilar: la animación es de entrada,
            // no un efecto que se repita cada vez que se sube y se baja.
            vigia.unobserve(e.target);
        });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });

    bloques.forEach(function (b) { vigia.observe(b); });
})();
