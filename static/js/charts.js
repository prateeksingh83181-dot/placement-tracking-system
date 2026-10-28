"""Chart.js rendering for admin placement reports."""

document.addEventListener("DOMContentLoaded", function () {
  if (!window.reportChartData) return;
  const data = window.reportChartData;

  const branchCanvas = document.getElementById("branchPlacementChart");
  if (branchCanvas) {
    new Chart(branchCanvas, {
      type: "bar",
      data: { labels: data.branchLabels, datasets: [{ label: "Placement %", data: data.branchPercentages, backgroundColor: "#0d6efd" }] },
      options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, suggestedMax: 100, ticks: { callback: value => value + "%" } } } }
    });
  }

  const turnoutCanvas = document.getElementById("driveTurnoutChart");
  if (turnoutCanvas) {
    new Chart(turnoutCanvas, {
      type: "bar",
      data: { labels: data.turnoutLabels, datasets: [{ label: "Applicants", data: data.turnoutCounts, backgroundColor: "#198754" }] },
      options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } }
    });
  }

  const statusCanvas = document.getElementById("applicationStatusChart");
  if (statusCanvas) {
    new Chart(statusCanvas, {
      type: "doughnut",
      data: { labels: data.statusLabels, datasets: [{ data: data.statusCounts, backgroundColor: ["#6c757d", "#0dcaf0", "#0d6efd", "#198754", "#dc3545"] }] },
      options: { responsive: true, maintainAspectRatio: false }
    });
  }
});
