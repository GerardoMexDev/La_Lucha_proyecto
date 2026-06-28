// ── Switch de tema claro / oscuro ──────────────────────────────────────────────
(function () {
    var CLAVE = 'caja-chica-tema';

    function aplicarTema(tema) {
        document.documentElement.setAttribute('data-theme', tema);
        localStorage.setItem(CLAVE, tema);
        var icono = document.getElementById('icono-tema');
        var label = document.getElementById('label-tema');
        if (!icono || !label) return;
        icono.textContent = tema === 'dark' ? '☀' : '🌙';
        label.textContent = tema === 'dark' ? 'Claro' : 'Oscuro';
    }

    // Sincronizar el botón con el tema que ya aplicó el script inline del <head>
    aplicarTema(localStorage.getItem(CLAVE) || 'dark');

    var btn = document.getElementById('btn-tema');
    if (btn) {
        btn.addEventListener('click', function () {
            var actual = document.documentElement.getAttribute('data-theme') || 'dark';
            aplicarTema(actual === 'dark' ? 'light' : 'dark');
        });
    }
})();


// ── Filtro de categorías por tipo ──────────────────────────────────────────────
function filtrarCategoriasEnSelect(selectEl, tipo) {
    if (!selectEl || !tipo) return;
    Array.from(selectEl.options).forEach(function (opcion) {
        if (!opcion.value) return; // "— Sin categoría —" siempre visible
        var visible = opcion.dataset.tipo === tipo || opcion.dataset.tipo === 'ambos';
        opcion.hidden = !visible;
        if (!visible && opcion.selected) selectEl.value = '';
    });
}

document.addEventListener('DOMContentLoaded', function () {
    // Formulario principal
    var radios = document.querySelectorAll('#form-movimiento input[name="tipo"]');
    var selectCat = document.getElementById('categoria_id');
    if (radios.length && selectCat) {
        radios.forEach(function (radio) {
            radio.addEventListener('change', function () {
                filtrarCategoriasEnSelect(selectCat, this.value);
            });
        });
        var checked = document.querySelector('#form-movimiento input[name="tipo"]:checked');
        if (checked) filtrarCategoriasEnSelect(selectCat, checked.value);
    }

    // Modal: filtrar también cuando cambia el tipo en el modal
    var radiosModal = document.querySelectorAll('#form-editar input[name="tipo"]');
    var selectCatModal = document.getElementById('edit-categoria');
    if (radiosModal.length && selectCatModal) {
        radiosModal.forEach(function (radio) {
            radio.addEventListener('change', function () {
                filtrarCategoriasEnSelect(selectCatModal, this.value);
            });
        });
    }

    // Cerrar modal al hacer clic fuera del cuadro
    var overlay = document.getElementById('modal-editar');
    if (overlay) {
        overlay.addEventListener('click', function (e) {
            if (e.target === overlay) cerrarModal();
        });
    }
});


// ── Modal de edición ───────────────────────────────────────────────────────────
function abrirModalEditar(btn) {
    var modal = document.getElementById('modal-editar');
    var form  = document.getElementById('form-editar');
    if (!modal || !form) return;

    // URL de la acción del formulario
    form.action = '/movimiento/' + btn.dataset.id + '/editar';

    // Campos de texto y número
    document.getElementById('edit-fecha').value   = btn.dataset.fecha;
    document.getElementById('edit-monto').value   = btn.dataset.monto;
    document.getElementById('edit-concepto').value = btn.dataset.concepto;
    document.getElementById('edit-obs').value     = btn.dataset.obs;

    // Tipo (radio)
    var tipoRadio = form.querySelector('input[name="tipo"][value="' + btn.dataset.tipo + '"]');
    if (tipoRadio) tipoRadio.checked = true;

    // Moneda (radio)
    var monedaRadio = form.querySelector('input[name="moneda"][value="' + btn.dataset.moneda + '"]');
    if (monedaRadio) monedaRadio.checked = true;

    // Método de pago
    document.getElementById('edit-metodo').value = btn.dataset.metodo;

    // Categoría: filtrar primero según tipo, luego seleccionar
    var selectCat = document.getElementById('edit-categoria');
    filtrarCategoriasEnSelect(selectCat, btn.dataset.tipo);
    selectCat.value = btn.dataset.categoria;

    modal.hidden = false;
    document.body.style.overflow = 'hidden';
}

function cerrarModal() {
    var modal = document.getElementById('modal-editar');
    if (modal) modal.hidden = true;
    document.body.style.overflow = '';
}


// ── Toggle tabla de movimientos del día ────────────────────────────────────────
function toggleMovimientos(btn) {
    var tabla = document.getElementById('tabla-movimientos');
    if (!tabla) return;
    var visible = !tabla.hidden;
    tabla.hidden = visible;
    btn.textContent = (visible ? '▶' : '▼') + btn.textContent.slice(1);
}
