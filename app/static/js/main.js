// Filtra las opciones del select de categorías según el tipo (ingreso/egreso) seleccionado
document.addEventListener('DOMContentLoaded', function () {
    const radios = document.querySelectorAll('input[name="tipo"]');
    const selectCategoria = document.getElementById('categoria_id');

    if (!radios.length || !selectCategoria) return;

    function filtrarCategorias() {
        const tipoSeleccionado = document.querySelector('input[name="tipo"]:checked')?.value;
        if (!tipoSeleccionado) return;

        Array.from(selectCategoria.options).forEach(function (opcion) {
            if (!opcion.value) return; // la opción "— Sin categoría —" siempre visible
            const tipoOpcion = opcion.dataset.tipo;
            const visible = tipoOpcion === tipoSeleccionado || tipoOpcion === 'ambos';
            opcion.hidden = !visible;
            if (!visible && opcion.selected) {
                selectCategoria.value = '';
            }
        });
    }

    radios.forEach(function (radio) {
        radio.addEventListener('change', filtrarCategorias);
    });

    // Aplicar al cargar la página
    filtrarCategorias();
});
