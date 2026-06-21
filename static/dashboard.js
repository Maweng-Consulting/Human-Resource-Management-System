(() => {
  "use strict";

  const body = document.body;
  const sidebar = document.getElementById("sidebarMenu");
  const toggle = document.getElementById("sidebarToggle");
  const close = document.getElementById("sidebarClose");
  const backdrop = document.getElementById("sidebarBackdrop");
  const desktopQuery = window.matchMedia("(min-width: 992px)");

  const setMobileSidebar = (open) => {
    body.classList.toggle("ops-sidebar-open", open);
    if (backdrop) {
      backdrop.hidden = !open;
    }
    if (toggle) {
      toggle.setAttribute("aria-expanded", String(open));
    }
  };

  const setDesktopSidebar = (collapsed) => {
    body.classList.toggle("ops-sidebar-collapsed", collapsed);
    if (toggle) {
      toggle.setAttribute("aria-expanded", String(!collapsed));
    }
    try {
      window.localStorage.setItem("m6-sidebar-collapsed", collapsed ? "1" : "0");
    } catch (error) {
      // Storage can be disabled in private browsing.
    }
  };

  const syncMode = () => {
    if (desktopQuery.matches) {
      setMobileSidebar(false);
      let collapsed = false;
      try {
        collapsed = window.localStorage.getItem("m6-sidebar-collapsed") === "1";
      } catch (error) {
        collapsed = false;
      }
      body.classList.toggle("ops-sidebar-collapsed", collapsed);
      if (toggle) {
        toggle.setAttribute("aria-expanded", String(!collapsed));
      }
    } else {
      body.classList.remove("ops-sidebar-collapsed");
      setMobileSidebar(false);
    }
  };

  const toggleSidebar = () => {
    if (!sidebar) {
      return;
    }
    if (desktopQuery.matches) {
      setDesktopSidebar(!body.classList.contains("ops-sidebar-collapsed"));
    } else {
      setMobileSidebar(!body.classList.contains("ops-sidebar-open"));
    }
  };

  window.M6Sidebar = {
    close: () => setMobileSidebar(false),
    sync: syncMode,
    toggle: toggleSidebar
  };

  if (sidebar && toggle) {
    syncMode();
  }

  if (close) {
    close.onclick = () => setMobileSidebar(false);
  }

  if (backdrop) {
    backdrop.onclick = () => setMobileSidebar(false);
  }

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      setMobileSidebar(false);
    }
  });

  desktopQuery.addEventListener("change", syncMode);
  window.addEventListener("pageshow", syncMode);

  const chartEl = document.getElementById("myChart");
  if (chartEl && window.Chart) {
    new Chart(chartEl, {
      type: "line",
      data: {
        labels: ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
        datasets: [{
          data: [15339, 21345, 18483, 24003, 23489, 24092, 12034],
          tension: 0.3,
          backgroundColor: "transparent",
          borderColor: "#2f9e8f",
          borderWidth: 3,
          pointBackgroundColor: "#2f9e8f"
        }]
      },
      options: {
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            boxPadding: 3
          }
        }
      }
    });
  }
})();
