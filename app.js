
document.addEventListener("DOMContentLoaded", () => {

    // Colocar automáticamente la fecha actual.

    const campoFecha = document.querySelector(
        'input[name="fecha"]'
    );

    if (campoFecha && !campoFecha.value) {

        const ahora = new Date();

        campoFecha.value = new Date(
            ahora.getTime() -
            ahora.getTimezoneOffset() * 60000
        ).toISOString().slice(0, 10);

    }

});
