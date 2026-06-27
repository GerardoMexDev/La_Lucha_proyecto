// ── Switch de tema claro / oscuro ──────────────────────────────────────────────
(function () {
    var CLAVE = 'caja-chica-tema';

    function aplicarTema(tema) {
        document.documentElement.setAttribute('data-theme', tema);
        localStorage.setItem(CLAVE, tema);

        var icono = document.getElementById('icono-tema');
        var label = document.getElementById('label-tema');
        if (!icono || !label) return;

        if (tema === 'dark') {
            icono.textContent = '☀';
            label.textContent = 'Claro';
        } else {
            icono.textContent = '🌙';
            label.textContent = 'Oscuro';
        }
    }

    // Sincronizar el botón con el tema que ya aplicó el script inline del <head>
    var temaActual = localStorage.getItem(CLAVE) || 'dark';
    aplicarTema(temaActual);

    var btn = document.getElementById('btn-tema');
    if (btn) {
        btn.addEventListener('click', function () {
            var actual = document.documentElement.getAttribute('data-theme') || 'dark';
            aplicarTema(actual === 'dark' ? 'light' : 'dark');
        });
    }
})();


// ── Filtro de categorías por tipo (ingreso / egreso) ───────────────────────────
document.addEventListener('DOMContentLoaded', function () {
    var radios = document.querySelectorAll('input[name="tipo"]');
    var selectCategoria = document.getElementById('categoria_id');

    if (!radios.length || !selectCategoria) return;

    function filtrarCategorias() {
        var checked = document.querySelector('input[name="tipo"]:checked');
        if (!checked) return;
        var tipoSeleccionado = checked.value;

        Array.from(selectCategoria.options).forEach(function (opcion) {
            if (!opcion.value) return; // "— Sin categoría —" siempre visible
            var visible = opcion.dataset.tipo === tipoSeleccionado || opcion.dataset.tipo === 'ambos';
            opcion.hidden = !visible;
            if (!visible && opcion.selected) {
                selectCategoria.value = '';
            }
        });
    }

    radios.forEach(function (radio) {
        radio.addEventListener('change', filtrarCategorias);
    });

    filtrarCategorias();
});
