document.addEventListener("DOMContentLoaded", () => {
  const modalElement = document.getElementById("confirm-action-modal");
  const modalTitle = document.getElementById("confirm-action-title");
  const modalMessage = document.getElementById("confirm-action-message");
  const modalSubmitButton = document.getElementById("confirm-action-submit");

  if (!modalElement || !modalTitle || !modalMessage || !modalSubmitButton) {
    return;
  }

  let pendingForm = null;
  let pendingSubmitName = "";
  let pendingSubmitValue = "";

  document.querySelectorAll("[data-confirm-submit]").forEach((button) => {
    button.addEventListener("click", () => {
      const formId = button.getAttribute("data-confirm-submit");
      const title = button.getAttribute("data-confirm-title") || "Confirm action";
      const message =
        button.getAttribute("data-confirm-message") ||
        "Are you sure you want to continue?";
      const confirmLabel =
        button.getAttribute("data-confirm-label") || "Confirm";

      pendingForm = document.getElementById(formId);
      pendingSubmitName = button.getAttribute("data-confirm-submit-name") || "";
      pendingSubmitValue = button.getAttribute("data-confirm-submit-value") || "";

      if (!pendingForm) {
        return;
      }

      modalTitle.textContent = title;
      modalMessage.textContent = message;
      modalSubmitButton.textContent = confirmLabel;
    });
  });

  modalSubmitButton.addEventListener("click", () => {
    if (!pendingForm) {
      return;
    }

    if (pendingSubmitName) {
      let submitMarker = pendingForm.querySelector(
        'input[data-confirm-submit-marker="true"]'
      );

      if (!submitMarker) {
        submitMarker = document.createElement("input");
        submitMarker.type = "hidden";
        submitMarker.setAttribute("data-confirm-submit-marker", "true");
        pendingForm.appendChild(submitMarker);
      }

      submitMarker.name = pendingSubmitName;
      submitMarker.value = pendingSubmitValue || "1";
    }

    if (typeof pendingForm.requestSubmit === "function") {
      pendingForm.requestSubmit();
    } else {
      pendingForm.submit();
    }
  });
});
