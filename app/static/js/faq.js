/**
 * DAR - FAQ Page Accessible Accordion Script
 * Supports keyboard navigation, single-panel expansion, and aria state management.
 */
document.addEventListener("DOMContentLoaded", () => {
  const triggers = Array.from(document.querySelectorAll(".faq-trigger"));

  triggers.forEach((trigger, index) => {
    trigger.addEventListener("click", () => {
      toggleFaq(trigger, triggers);
    });

    // Keyboard navigation (ArrowUp, ArrowDown, Home, End)
    trigger.addEventListener("keydown", (e) => {
      let targetIndex = null;
      if (e.key === "ArrowDown") {
        e.preventDefault();
        targetIndex = (index + 1) % triggers.length;
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        targetIndex = (index - 1 + triggers.length) % triggers.length;
      } else if (e.key === "Home") {
        e.preventDefault();
        targetIndex = 0;
      } else if (e.key === "End") {
        e.preventDefault();
        targetIndex = triggers.length - 1;
      }

      if (targetIndex !== null) {
        triggers[targetIndex].focus();
      }
    });
  });
});

function toggleFaq(selectedTrigger, allTriggers) {
  const isCurrentlyOpen = selectedTrigger.getAttribute("aria-expanded") === "true";
  const controlsId = selectedTrigger.getAttribute("aria-controls");
  const selectedPanel = document.getElementById(controlsId);
  const selectedChevron = selectedTrigger.querySelector(".faq-chevron");

  // Close all panels first (single panel open at a time)
  allTriggers.forEach((trigger) => {
    trigger.setAttribute("aria-expanded", "false");
    trigger.style.backgroundColor = "transparent";
    const panelId = trigger.getAttribute("aria-controls");
    const panel = document.getElementById(panelId);
    if (panel) {
      panel.hidden = true;
    }
    const chevron = trigger.querySelector(".faq-chevron");
    if (chevron) {
      chevron.style.transform = "rotate(0deg)";
    }
  });

  // If it was not open, open it
  if (!isCurrentlyOpen && selectedPanel) {
    selectedTrigger.setAttribute("aria-expanded", "true");
    selectedTrigger.style.backgroundColor = "var(--bg-soft)";
    selectedPanel.hidden = false;
    if (selectedChevron) {
      selectedChevron.style.transform = "rotate(180deg)";
    }
  }
}
