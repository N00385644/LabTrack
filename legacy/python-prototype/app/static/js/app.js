/* Interacciones de LabTrack (sin dependencias externas). */
(function () {
  "use strict";

  // Cierre manual y automático de mensajes flash.
  document.querySelectorAll(".flash").forEach(function (flash) {
    var close = flash.querySelector(".flash-close");
    function hide() {
      flash.classList.add("is-hiding");
      window.setTimeout(function () { flash.remove(); }, 220);
    }
    if (close) {
      close.addEventListener("click", hide);
    }
    window.setTimeout(hide, 6500);
  });

  // Confirmación para acciones sensibles (aprobaciones/devoluciones).
  document.querySelectorAll("[data-confirm]").forEach(function (element) {
    element.addEventListener("click", function (event) {
      if (!window.confirm(element.getAttribute("data-confirm"))) {
        event.preventDefault();
      }
    });
  });

  // Mostrar / ocultar contraseña.
  document.querySelectorAll("[data-toggle-password]").forEach(function (button) {
    button.addEventListener("click", function () {
      var input = document.getElementById(button.getAttribute("data-toggle-password"));
      if (!input) return;
      var isPassword = input.type === "password";
      input.type = isPassword ? "text" : "password";
      button.textContent = isPassword ? "Ocultar" : "Ver";
    });
  });

  // Resumen dinámico del equipo seleccionado en el formulario de reserva.
  var equipmentSelect = document.querySelector("[data-equipment-select]");
  var summary = document.querySelector("[data-equipment-summary]");
  if (equipmentSelect && summary) {
    var nameEl = summary.querySelector("[data-summary-name]");
    var categoryEl = summary.querySelector("[data-summary-category]");
    var codeEl = summary.querySelector("[data-summary-code]");
    var locationEl = summary.querySelector("[data-summary-location]");

    function updateSummary() {
      var option = equipmentSelect.options[equipmentSelect.selectedIndex];
      if (!option || !option.value) return;
      nameEl.textContent = option.getAttribute("data-name") || "Equipo";
      categoryEl.textContent = option.getAttribute("data-category") || "";
      codeEl.textContent = option.getAttribute("data-code") || "—";
      locationEl.textContent = option.getAttribute("data-location") || "—";
    }
    equipmentSelect.addEventListener("change", updateSummary);
    updateSummary();
  }

  // Validación previa del rango horario.
  var startInput = document.getElementById("start_time");
  var endInput = document.getElementById("end_time");
  if (startInput && endInput) {
    function validateRange() {
      if (startInput.value && endInput.value && endInput.value <= startInput.value) {
        endInput.setCustomValidity("La hora de fin debe ser posterior a la hora de inicio.");
      } else {
        endInput.setCustomValidity("");
      }
    }
    startInput.addEventListener("change", validateRange);
    endInput.addEventListener("change", validateRange);
  }
})();
