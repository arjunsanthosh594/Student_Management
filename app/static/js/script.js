/* ============================================================
   Student Management System — Main Client Script (Phase 2 Enhanced)
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {

  /* ------------------------------------------------------------
     1. Sidebar Navigation & Responsive Toggle
     ------------------------------------------------------------ */
  const sidebar    = document.getElementById("sidebar");
  const backdrop   = document.getElementById("sidebar-backdrop");
  const toggleBtn  = document.getElementById("sidebar-toggle");

  function openSidebar() {
    sidebar?.classList.add("open");
    backdrop?.classList.add("show");
    document.body.style.overflow = "hidden";
  }

  function closeSidebar() {
    sidebar?.classList.remove("open");
    backdrop?.classList.remove("show");
    document.body.style.overflow = "";
  }

  toggleBtn?.addEventListener("click", () => {
    sidebar?.classList.contains("open") ? closeSidebar() : openSidebar();
  });

  backdrop?.addEventListener("click", closeSidebar);

  // Close sidebar on window resize to desktop
  window.addEventListener("resize", () => {
    if (window.innerWidth >= 992 && sidebar?.classList.contains("open")) {
      closeSidebar();
    }
  });

  // Active link highlighter
  const currentPath = window.location.pathname;
  document.querySelectorAll(".sidebar-nav .nav-link").forEach(link => {
    const href = link.getAttribute("href");
    if (href && currentPath === href) {
      link.classList.add("active");
    } else if (href && href !== "/" && href !== "/admin/dashboard" && href !== "/student/dashboard" && currentPath.startsWith(href)) {
      link.classList.add("active");
    }
  });

  /* ------------------------------------------------------------
     2. Password Visibility Toggle
     ------------------------------------------------------------ */
  document.querySelectorAll(".password-toggle").forEach(btn => {
    btn.addEventListener("click", () => {
      const input = document.querySelector(btn.dataset.target);
      if (!input) return;
      const isText = input.type === "text";
      input.type = isText ? "password" : "text";
      const icon = btn.querySelector("i");
      if (icon) {
        icon.className = isText ? "bi bi-eye" : "bi bi-eye-slash";
      }
    });
  });

  /* ------------------------------------------------------------
     3. Dual-Role Login Tab Switcher
     ------------------------------------------------------------ */
  const roleTabs       = document.querySelectorAll(".role-tab");
  const roleInput      = document.getElementById("role-input");
  const usernameLabel  = document.getElementById("usernameLabel");
  const usernameInput  = document.getElementById("username");
  const usernameHelp   = document.getElementById("usernameHelp");
  const passwordHelp   = document.getElementById("passwordHelp");
  const submitBtnText  = document.getElementById("submitBtnText");

  roleTabs.forEach(tab => {
    tab.addEventListener("click", () => {
      roleTabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      const role = tab.dataset.role;
      if (roleInput) roleInput.value = role;

      if (role === "admin") {
        if (usernameLabel) usernameLabel.innerHTML = '<i class="bi bi-shield-lock me-1 text-primary"></i>Admin Username';
        if (usernameInput) usernameInput.placeholder = "Enter administrator username";
        if (usernameHelp) usernameHelp.innerHTML = 'Default: <code>admin</code>';
        if (passwordHelp) passwordHelp.innerHTML = 'Default: <code>Admin@1234</code>';
        if (submitBtnText) submitBtnText.innerText = 'Sign In as Administrator';
      } else if (role === "student") {
        if (usernameLabel) usernameLabel.innerHTML = '<i class="bi bi-mortarboard me-1 text-primary"></i>Student ID / Username';
        if (usernameInput) usernameInput.placeholder = "e.g. SMS-202412345";
        if (usernameHelp) usernameHelp.innerHTML = 'Your assigned ID (from registration / seed script)';
        if (passwordHelp) passwordHelp.innerHTML = 'Default: <code>Student@123</code>';
        if (submitBtnText) submitBtnText.innerText = 'Sign In as Student';
      }
    });
  });

  /* ------------------------------------------------------------
     4. Delete Form Confirmation Dialogs
     ------------------------------------------------------------ */
  document.querySelectorAll(".confirm-delete").forEach(form => {
    form.addEventListener("submit", (e) => {
      const name = form.dataset.name || "this record";
      if (!confirm(`Are you sure you want to delete ${name}?\n\nThis action cannot be undone.`)) {
        e.preventDefault();
      }
    });
  });

  /* ------------------------------------------------------------
     5. Attendance Marking Visual Toggles & Bulk Select
     ------------------------------------------------------------ */
  document.querySelectorAll(".att-status-radio").forEach(radio => {
    radio.addEventListener("change", () => {
      const row = radio.closest("tr");
      if (!row) return;
      row.classList.remove("table-success", "table-danger");
      if (radio.value === "Present") row.classList.add("table-success");
      if (radio.value === "Absent")  row.classList.add("table-danger");
    });
    // Trigger on load for pre-checked
    if (radio.checked) {
      const row = radio.closest("tr");
      if (row) {
        if (radio.value === "Present") row.classList.add("table-success");
        if (radio.value === "Absent")  row.classList.add("table-danger");
      }
    }
  });

  document.getElementById("mark-all-present")?.addEventListener("click", () => {
    document.querySelectorAll('input[type=radio][value=Present]').forEach(r => {
      r.checked = true;
      r.dispatchEvent(new Event("change"));
    });
  });

  document.getElementById("mark-all-absent")?.addEventListener("click", () => {
    document.querySelectorAll('input[type=radio][value=Absent]').forEach(r => {
      r.checked = true;
      r.dispatchEvent(new Event("change"));
    });
  });

  /* ------------------------------------------------------------
     6. Profile Picture Live Preview & Validation
     ------------------------------------------------------------ */
  const profileInput = document.getElementById("profile_picture");
  const profilePreview = document.getElementById("profile-preview");
  if (profileInput && profilePreview) {
    profileInput.addEventListener("change", () => {
      const file = profileInput.files[0];
      if (file) {
        // Validate size (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
          alert("File is too large! Maximum image size allowed is 5 MB.");
          profileInput.value = "";
          return;
        }
        const reader = new FileReader();
        reader.onload = e => {
          profilePreview.src = e.target.result;
          profilePreview.style.display = "block";
        };
        reader.readAsDataURL(file);
      }
    });
  }

  /* ------------------------------------------------------------
     7. Auto-dismiss Flash Alerts
     ------------------------------------------------------------ */
  document.querySelectorAll(".alert-dismissible").forEach(alert => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      bsAlert?.close();
    }, 6000);
  });

  /* ------------------------------------------------------------
     8. Bootstrap Tooltips
     ------------------------------------------------------------ */
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
    new bootstrap.Tooltip(el, { trigger: "hover" });
  });

  /* ------------------------------------------------------------
     9. Chart.js: Enrolment Trend (Bar Chart)
     ------------------------------------------------------------ */
  const chartCanvas = document.getElementById("enrolment-chart");
  if (chartCanvas && typeof Chart !== "undefined") {
    try {
      const labels = JSON.parse(chartCanvas.dataset.labels || "[]");
      const values = JSON.parse(chartCanvas.dataset.values || "[]");

      new Chart(chartCanvas, {
        type: "bar",
        data: {
          labels,
          datasets: [{
            label: "Enrolments",
            data: values,
            backgroundColor: "rgba(26, 86, 219, 0.85)",
            hoverBackgroundColor: "#1240b0",
            borderRadius: 6,
            maxBarThickness: 38,
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              backgroundColor: "rgba(15, 23, 42, 0.9)",
              padding: 10,
              titleFont: { size: 12, family: "'Inter', sans-serif" },
              bodyFont: { size: 13, family: "'Inter', sans-serif" },
              displayColors: false,
              callbacks: {
                label: ctx => ` ${ctx.parsed.y} student${ctx.parsed.y !== 1 ? "s" : ""} admitted`
              }
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              ticks: {
                stepSize: 1,
                font: { size: 11, family: "'Inter', sans-serif" },
                color: "#64748b"
              },
              grid: {
                color: "rgba(226, 232, 240, 0.8)",
                drawBorder: false
              }
            },
            x: {
              ticks: {
                font: { size: 11, family: "'Inter', sans-serif" },
                color: "#64748b"
              },
              grid: { display: false }
            }
          }
        }
      });
    } catch (e) {
      console.error("Enrolment chart render error:", e);
    }
  }

  /* ------------------------------------------------------------
     10. Chart.js: Attendance Donut Chart
     ------------------------------------------------------------ */
  const attCanvas = document.getElementById("attendance-chart");
  if (attCanvas && typeof Chart !== "undefined") {
    try {
      const present = parseInt(attCanvas.dataset.present || "0", 10);
      const absent  = parseInt(attCanvas.dataset.absent  || "0", 10);

      if (present + absent > 0) {
        new Chart(attCanvas, {
          type: "doughnut",
          data: {
            labels: ["Present", "Absent"],
            datasets: [{
              data: [present, absent],
              backgroundColor: ["#16a34a", "#dc2626"],
              hoverBackgroundColor: ["#15803d", "#b91c1c"],
              borderWidth: 2,
              borderColor: "#ffffff",
              hoverOffset: 4
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "70%",
            plugins: {
              legend: {
                position: "bottom",
                labels: {
                  boxWidth: 12,
                  font: { size: 11, family: "'Inter', sans-serif" },
                  padding: 12,
                  color: "#334155"
                }
              },
              tooltip: {
                backgroundColor: "rgba(15, 23, 42, 0.9)",
                padding: 10,
                callbacks: {
                  label: ctx => ` ${ctx.label}: ${ctx.raw} record${ctx.raw !== 1 ? "s" : ""}`
                }
              }
            }
          }
        });
      }
    } catch (e) {
      console.error("Attendance chart render error:", e);
    }
  }

});
