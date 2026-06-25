/* cell_tutor_links.js
   This script adds an "Ask AI Tutor about this block" link at
   the bottom of every Jupyter notebook cell. When clicked, the
   link opens the AI tutor bar and tells it which cell you're
   asking about so it can give a focused answer. */

(function () {
  // function that adds the link to ONE cell
  function addLinkToCell(cell) {
    // If this cell already has our link, skip it
    if (cell.querySelector(".ask-ai-tutor-link")) return;

    // Create a container <div> for the link
    var container = document.createElement("div");
    container.className = "ask-ai-tutor-link";

    // Create the <a> element (the actual clickable link)
    var a = document.createElement("a");
    a.href = "#";
    a.textContent = "Ask AI Tutor about this block";

    // When the link is clicked…
    a.addEventListener("click", function (e) {
      e.preventDefault();                    // don't actually navigate

      // Copy the cell so we can clean it up without changing the real page
      var clone = cell.cloneNode(true);
      // Remove any tutor links from the copy (we don't want "Ask AI Tutor…" in the text)
      var links = clone.querySelectorAll(".ask-ai-tutor-link");
      for (var i = 0; i < links.length; i++) links[i].remove();
      // Get the cell's text content (code + output, but not the link text)
      var cellText = (clone.textContent || "").trim();

      // Tell the tutor bar to open and remember this cell's content
      if (window.openTutorBar) window.openTutorBar(cellText);
    });

    // Put the link inside the container, then the container inside the cell
    container.appendChild(a);
    cell.appendChild(container);
  }

  // add links to any cells that already exist on the page
  var existing = document.querySelectorAll(".jp-Cell");
  for (var i = 0; i < existing.length; i++) addLinkToCell(existing[i]);

  // watch for NEW cells being added later
  // JupyterLite is a "single-page app" — cells are created by
  // JavaScript long after this script runs. A MutationObserver
  // is like a motion sensor for the page: it fires whenever new
  // HTML elements appear.
  var observer = new MutationObserver(function (mutations) {
    // mutations = a list of changes that just happened
    for (var i = 0; i < mutations.length; i++) {
      var added = mutations[i].addedNodes;   // the new elements
      for (var j = 0; j < added.length; j++) {
        // Ignore non-element nodes (text nodes, comments, etc.)
        if (added[j].nodeType !== 1) continue;

        // If the new element itself is a cell, add a link
        if (added[j].matches && added[j].matches(".jp-Cell")) {
          addLinkToCell(added[j]);
        }

        // If it contains cells inside it, add links to those too
        if (added[j].querySelectorAll) {
          var cells = added[j].querySelectorAll(".jp-Cell");
          for (var k = 0; k < cells.length; k++) addLinkToCell(cells[k]);
        }
      }
    }
  });

  // Start watching — check the whole page and everything inside it
  observer.observe(document.body, { childList: true, subtree: true });
})();
