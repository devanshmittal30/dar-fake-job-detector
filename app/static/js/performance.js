/**
 * DAR - Model Performance Page Script
 * Fetches /api/metrics and verifies/populates the evaluation metrics table.
 */
document.addEventListener("DOMContentLoaded", () => {
  loadMetricsData();
});

async function loadMetricsData() {
  try {
    const response = await fetch("/api/metrics");
    if (!response.ok) return;
    const data = await response.json();

    const metrics = data.metrics || {};
    const config = data.config || {};

    const lrTest = metrics.lr ? metrics.lr.test : null;
    const rfTest = metrics.rf ? metrics.rf.test : null;

    if (lrTest) {
      setMetricText("m-lr-acc", formatPercent(lrTest.accuracy));
      setMetricText("m-lr-prec", formatPercent(lrTest.precision));
      setMetricText("m-lr-rec", formatPercent(lrTest.recall));
      setMetricText("m-lr-f1", formatPercent(lrTest.f1));
      setMetricText("m-lr-roc", formatDecimal(lrTest.roc_auc, 3));
      setMetricText("m-lr-pr", formatDecimal(lrTest.pr_auc, 3));
      setMetricText("m-lr-thresh", formatDecimal(lrTest.threshold, 2));
    }

    if (rfTest) {
      setMetricText("m-rf-acc", formatPercent(rfTest.accuracy));
      setMetricText("m-rf-prec", formatPercent(rfTest.precision));
      setMetricText("m-rf-rec", formatPercent(rfTest.recall));
      setMetricText("m-rf-f1", formatPercent(rfTest.f1));
      setMetricText("m-rf-roc", formatDecimal(rfTest.roc_auc, 3));
      setMetricText("m-rf-pr", formatDecimal(rfTest.pr_auc, 3));
      setMetricText("m-rf-thresh", formatDecimal(rfTest.threshold, 2));
    }

    // External test check
    const lrExt = metrics.lr ? metrics.lr.external_test : null;
    const extStatus = document.getElementById("external-test-status");
    if (extStatus) {
      if (lrExt) {
        extStatus.textContent = `Results recorded: Accuracy ${(lrExt.accuracy * 100).toFixed(1)}%, F1 ${(lrExt.f1 * 100).toFixed(1)}%.`;
      } else {
        extStatus.textContent = "Status: No external test evaluation results recorded in models/metrics.json yet.";
      }
    }
  } catch (err) {
    console.error("Failed to load /api/metrics:", err);
  }
}

function formatPercent(val) {
  if (val === null || val === undefined) return "n/a";
  return (val * 100).toFixed(1) + "%";
}

function formatDecimal(val, places = 3) {
  if (val === null || val === undefined) return "n/a";
  return val.toFixed(places);
}

function setMetricText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}
