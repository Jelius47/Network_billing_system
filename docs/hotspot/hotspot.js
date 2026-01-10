// HotSpot utility functions
function getQueryParam(name) {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get(name);
}

function formatCurrency(amount) {
  return new Intl.NumberFormat("sw-TZ", {
    style: "currency",
    currency: "TZS",
    minimumFractionDigits: 0,
  }).format(amount);
}

function formatBytes(bytes) {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

function showLoading(show = true) {
  const loadingEl = document.getElementById("loading");
  if (loadingEl) {
    loadingEl.style.display = show ? "block" : "none";
  }
}

function showMessage(message, type = "info") {
  const messageEl = document.createElement("div");
  messageEl.className = `message ${type}-message`;
  messageEl.textContent = message;
  messageEl.style.margin = "10px 0";
  messageEl.style.padding = "10px";
  messageEl.style.borderRadius = "4px";

  if (type === "error") {
    messageEl.style.background = "#fef2f2";
    messageEl.style.color = "#dc2626";
    messageEl.style.border = "1px solid #fecaca";
  } else if (type === "success") {
    messageEl.style.background = "#f0fdf4";
    messageEl.style.color = "#16a34a";
    messageEl.style.border = "1px solid #bbf7d0";
  } else {
    messageEl.style.background = "#f3f4f6";
    messageEl.style.color = "#4b5563";
    messageEl.style.border = "1px solid #e5e7eb";
  }

  const container = document.querySelector(".form-container") || document.body;
  container.insertBefore(messageEl, container.firstChild);

  setTimeout(() => {
    messageEl.remove();
  }, 5000);
}

// Form validation
function validateForm(formId) {
  const form = document.getElementById(formId);
  if (!form) return true;

  const inputs = form.querySelectorAll("input[required], select[required]");
  let isValid = true;

  inputs.forEach((input) => {
    if (!input.value.trim()) {
      input.style.borderColor = "#dc2626";
      isValid = false;

      input.addEventListener(
        "input",
        function () {
          this.style.borderColor = "#d1d5db";
        },
        { once: true },
      );
    }
  });

  return isValid;
}

// Session management
function checkSession() {
  const sessionWarning = localStorage.getItem("sessionWarning");
  if (sessionWarning) {
    const remaining = parseInt(sessionWarning);
    if (remaining < 300) {
      // 5 minutes warning
      showMessage(
        `Session expires in ${Math.floor(remaining / 60)} minutes`,
        "warning",
      );
    }
  }
}

// Initialize on DOM ready
document.addEventListener("DOMContentLoaded", function () {
  // Focus first input in active form
  const activeForm = document.querySelector("form");
  if (activeForm) {
    const firstInput = activeForm.querySelector(
      'input[type="text"], input[type="email"]',
    );
    if (firstInput && !firstInput.value) {
      setTimeout(() => firstInput.focus(), 100);
    }
  }

  // Check session periodically
  setInterval(checkSession, 60000);
  checkSession();
});
