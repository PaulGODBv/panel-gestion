document.addEventListener('DOMContentLoaded', function() {
    // 1. Mockup Updater
    const textInput = document.getElementById('id_text');
    const readingInput = document.getElementById('id_reading_text');
    const levelSelect = document.getElementById('id_level');
    const mockupText = document.getElementById('mockup-text');
    const mockupReading = document.getElementById('mockup-reading');
    const mockupLevel = document.getElementById('mockup-level');
    const mockupOptions = document.getElementById('mockup-options');

    function updateMockup() {
        if (textInput) mockupText.innerText = textInput.value || 'Aquí aparecerá el enunciado...';
        if (readingInput) {
            if (readingInput.value) {
                mockupReading.innerText = readingInput.value;
                mockupReading.style.display = 'block';
            } else {
                mockupReading.style.display = 'none';
            }
        }
        if (levelSelect && levelSelect.options[levelSelect.selectedIndex]) {
            mockupLevel.innerText = levelSelect.options[levelSelect.selectedIndex].text;
        }

        // Options
        const optionInputs = document.querySelectorAll('[id^="id_options-"][id$="-text"]');
        mockupOptions.innerHTML = '';
        optionInputs.forEach((opt, idx) => {
            if (opt.value) {
                const div = document.createElement('div');
                div.className = 'rt-phone__option';
                div.innerText = opt.value;
                mockupOptions.appendChild(div);
            }
        });
    }

    if (textInput) textInput.addEventListener('input', updateMockup);
    if (readingInput) readingInput.addEventListener('input', updateMockup);
    if (levelSelect) levelSelect.addEventListener('change', updateMockup);
    
    // Listen to option inputs (event delegation since they can be added dynamically)
    document.addEventListener('input', function(e) {
        if (e.target && e.target.id && e.target.id.match(/^id_options-.*-text$/)) {
            updateMockup();
        }
    });

    updateMockup();

    // 2. Inline Validation
    if (textInput) {
        const errorSpan = document.createElement('span');
        errorSpan.className = 'inline-error';
        errorSpan.innerText = 'Este campo es obligatorio';
        errorSpan.style.display = 'none';
        textInput.parentNode.appendChild(errorSpan);

        textInput.addEventListener('blur', function() {
            if (!this.value.trim()) {
                errorSpan.style.display = 'block';
                this.classList.add('border-red-500');
            } else {
                errorSpan.style.display = 'none';
                this.classList.remove('border-red-500');
            }
        });
    }

    // 3. Toasts flotantes en envío de formulario (interceptar submit)
    const form = document.getElementById('question_form') || document.getElementById('level_form');
    if (form) {
        form.addEventListener('submit', function(e) {
            // Inline validation check
            if (textInput && !textInput.value.trim()) {
                e.preventDefault();
                textInput.focus();
                return;
            }

            // Para cumplir con el requerimiento de NO recargar y mostrar Toast flotante
            e.preventDefault();
            const submitBtn = document.activeElement;
            const formData = new FormData(form);
            
            // Append the button that was clicked so Django knows what action to take (e.g. _save, _addanother, _continue)
            if (submitBtn && submitBtn.name) {
                formData.append(submitBtn.name, submitBtn.value);
            } else {
                formData.append('_save', 'Grabar');
            }

            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                if (response.ok || response.redirected) {
                    Toastify({
                        text: "✅ Guardado exitosamente",
                        duration: 3000,
                        close: true,
                        gravity: "top",
                        position: "right",
                        style: {
                            background: "#10b981", // green-500
                        }
                    }).showToast();
                    
                    // Si redirige, seguimos la redirección después de un momento para que se vea el toast,
                    // O si querían 100% sin recarga, no redirigimos, pero Django Admin no funciona bien como SPA.
                    // Para ser seguros, redirigiremos si es necesario, o recargaremos.
                    setTimeout(() => {
                        if (response.url && response.url !== window.location.href) {
                            window.location.href = response.url;
                        } else if (submitBtn.name === '_save') {
                            window.location.href = '../';
                        }
                    }, 1000);
                } else {
                    Toastify({
                        text: "❌ Error al guardar. Verifica los campos.",
                        duration: 3000,
                        close: true,
                        gravity: "top",
                        position: "right",
                        style: {
                            background: "#ef4444", // red-500
                        }
                    }).showToast();
                    // We might need to render form errors here, but for simplicity we rely on the toast.
                }
            })
            .catch(error => {
                Toastify({
                    text: "❌ Error de conexión",
                    duration: 3000,
                    close: true,
                    gravity: "top",
                    position: "right",
                    style: { background: "#ef4444" }
                }).showToast();
            });
        });
    }
});
