/**
 * DAR - Scam Awareness Page Script
 * Fetches /api/stats, renders Chart.js charts, and drives the 10-tip carousel.
 */
document.addEventListener("DOMContentLoaded", () => {
  initTipsCarousel();
  loadAwarenessStats();
});

// 10 Safety Tips strictly from docs/02_UI_UX_SPEC.md section 13
const SAFETY_TIPS = [
  {
    title: "Real employers never ask for money",
    desc: "Registration, training, kit or security deposit fees are a scam sign."
  },
  {
    title: "Too good to be true",
    desc: "Very high pay for simple work from home."
  },
  {
    title: "Contact only on WhatsApp or Telegram",
    desc: "Contact only on WhatsApp or Telegram, with no official company email or website."
  },
  {
    title: "Offers from free email addresses",
    desc: "Offers from free email addresses (gmail, yahoo) instead of a company domain."
  },
  {
    title: "No interview, instant offer",
    desc: "Hired without a proper selection process."
  },
  {
    title: "Asks for bank details, Aadhaar, PAN or OTP",
    desc: "Never share these to get a job."
  },
  {
    title: "Urgency pressure",
    desc: "\"Pay today or lose the seat.\""
  },
  {
    title: "Check the company",
    desc: "Search its name on the official website and LinkedIn."
  },
  {
    title: "Typos and vague details",
    desc: "Missing address, job role or company name."
  },
  {
    title: "Already paid?",
    desc: "Call 1930 and report at cybercrime.gov.in."
  }
];

let currentTipIndex = 0;

function initTipsCarousel() {
  const prevBtn = document.getElementById("tip-prev-btn");
  const nextBtn = document.getElementById("tip-next-btn");
  const indicatorsContainer = document.getElementById("tip-indicators");
  const carouselCard = document.getElementById("tip-carousel-card");

  if (!carouselCard || !prevBtn || !nextBtn) return;

  // Build indicator dots
  indicatorsContainer.innerHTML = "";
  SAFETY_TIPS.forEach((_, idx) => {
    const dot = document.createElement("button");
    dot.type = "button";
    dot.setAttribute("aria-label", `Go to rule ${idx + 1}`);
    dot.style.width = "10px";
    dot.style.height = "10px";
    dot.style.borderRadius = "50%";
    dot.style.border = "none";
    dot.style.padding = "0";
    dot.style.cursor = "pointer";
    dot.style.backgroundColor = idx === 0 ? "var(--primary)" : "var(--border)";
    dot.style.transition = "background-color 0.2s ease";
    dot.addEventListener("click", () => showTip(idx));
    indicatorsContainer.appendChild(dot);
  });

  prevBtn.addEventListener("click", () => {
    showTip((currentTipIndex - 1 + SAFETY_TIPS.length) % SAFETY_TIPS.length);
  });

  nextBtn.addEventListener("click", () => {
    showTip((currentTipIndex + 1) % SAFETY_TIPS.length);
  });

  // Keyboard navigation
  carouselCard.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft") {
      e.preventDefault();
      showTip((currentTipIndex - 1 + SAFETY_TIPS.length) % SAFETY_TIPS.length);
    } else if (e.key === "ArrowRight") {
      e.preventDefault();
      showTip((currentTipIndex + 1) % SAFETY_TIPS.length);
    }
  });

  showTip(0);
}

function showTip(index) {
  currentTipIndex = index;
  const tip = SAFETY_TIPS[index];
  
  const badge = document.getElementById("tip-badge");
  const title = document.getElementById("tip-title");
  const desc = document.getElementById("tip-desc");
  const indicators = document.querySelectorAll("#tip-indicators button");

  if (badge) badge.textContent = `Rule ${index + 1} of ${SAFETY_TIPS.length}`;
  if (title) title.textContent = tip.title;
  if (desc) desc.textContent = tip.desc;

  indicators.forEach((dot, idx) => {
    dot.style.backgroundColor = idx === index ? "var(--primary)" : "var(--border)";
    dot.style.transform = idx === index ? "scale(1.2)" : "scale(1)";
  });
}

async function loadAwarenessStats() {
  try {
    const response = await fetch("/api/stats");
    if (!response.ok) return;
    const data = await response.json();

    renderYearlyLossesChart(data.yearly_losses);
    renderLossTypesChart(data.fake_investment_share_2025);
  } catch (err) {
    console.error("Failed to load awareness stats:", err);
  }
}

function renderYearlyLossesChart(yearlyLosses) {
  const canvas = document.getElementById("yearly-losses-chart");
  if (!canvas || !window.Chart || !yearlyLosses) return;

  const labels = yearlyLosses.map(item => item.year);
  const values = yearlyLosses.map(item => item.amount_crore);

  new window.Chart(canvas, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Reported Losses (₹ Crore)",
          data: values,
          backgroundColor: [
            "rgba(29, 78, 216, 0.75)",
            "rgba(29, 78, 216, 0.85)",
            "rgba(29, 78, 216, 0.95)",
            "rgba(29, 78, 216, 0.55)"
          ],
          borderColor: "rgb(29, 78, 216)",
          borderWidth: 1.5,
          borderRadius: 6,
          maxBarThickness: 54
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ₹${ctx.parsed.y.toLocaleString("en-IN")} Crore`
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: (val) => `₹${val.toLocaleString("en-IN")} Cr`
          },
          grid: {
            color: "rgba(0, 0, 0, 0.05)"
          }
        },
        x: {
          grid: { display: false }
        }
      }
    }
  });
}

function renderLossTypesChart(investmentShare) {
  const canvas = document.getElementById("loss-types-chart");
  if (!canvas || !window.Chart) return;

  const fakeInvestShare = investmentShare ? investmentShare.percentage : 76;
  const otherShare = 100 - fakeInvestShare;

  new window.Chart(canvas, {
    type: "doughnut",
    data: {
      labels: ["Fake investment schemes", "Other online financial fraud"],
      datasets: [
        {
          data: [fakeInvestShare, otherShare],
          backgroundColor: ["#DC2626", "#94A3B8"],
          borderWidth: 2,
          borderColor: "#FFFFFF"
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "68%",
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            boxWidth: 14,
            padding: 16,
            font: { size: 12 }
          }
        },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.label}: ${ctx.parsed}%`
          }
        }
      }
    }
  });
}
