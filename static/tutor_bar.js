(function () {
  var btn = document.getElementById("tutor-bar-btn");
  var panel = document.getElementById("tutor-bar-panel");
  var close = document.getElementById("tutor-bar-close");
  var output = document.getElementById("tutor-bar-output");
  var input = document.getElementById("tutor-bar-input");
  var send = document.getElementById("tutor-bar-send");
  var promptLabel = document.getElementById("tutor-prompt-label");

  var API_URL = (window.API_BASE || "") + "/api/tutor-chat";

  var cellNum = 1;
  var tutor_history = [];
  var loadingEl = null;
  var focusedCell = null;

  function toggle() {
    panel.classList.toggle("open");
    btn.classList.toggle("hidden");
    if (panel.classList.contains("open")) {
      input.focus();
    }
  }

  btn.addEventListener("click", toggle);
  close.addEventListener("click", toggle);

  function addBlock(label, text, isError) {
    var block = document.createElement("div");
    block.className = "tutor-block";
    var lbl = document.createElement("div");
    lbl.className = "tutor-label" + (isError ? " error" : "");
    lbl.textContent = label;
    block.appendChild(lbl);
    var content = document.createElement("div");
    content.className = "tutor-content";
    if (label.charAt(0) === "O" && !isError) {
      content.innerHTML = marked.parse(text);
      if (typeof renderMathInElement === "function") {
        renderMathInElement(content, {
          delimiters: [
            { left: "$$", right: "$$", display: true },
            { left: "$", right: "$", display: false },
          ],
        });
      }
    } else {
      content.textContent = text;
    }
    block.appendChild(content);
    output.appendChild(block);
    output.scrollTop = output.scrollHeight;
    return block;
  }

  function getPageText() {
    var body = document.body;
    var clone = body.cloneNode(true);
    var exclude = clone.querySelector("#tutor-bar-wrap, #ai-sidebar-wrap");
    if (exclude) exclude.remove();
    var els = clone.querySelectorAll("script,style,nav,header,footer,#spaghettios-banner,.ask-ai-tutor-link");
    for (var i = 0; i < els.length; i++) els[i].remove();
    var text = (clone.textContent || "").trim();
    if (focusedCell) {
      text = "--- Cell of interest ---\n" + focusedCell + "\n--- Rest of page ---\n\n" + text;
    }
    return text.slice(0, 8000);
  }

  function ask() {
    var q = input.value.trim();
    if (!q) return;
    input.value = "";

    var promptStr = "In [" + cellNum + "]:";
    promptLabel.textContent = "In [" + (cellNum + 1) + "]:";
    addBlock(promptStr, q);
    loadingEl = addBlock("Out [" + cellNum + "]:", "Thinking...");
    send.disabled = true;

    fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: q, context: getPageText(), history: tutor_history }),
    })
      .then(function (r) {
        if (!r.ok) {
          return r.text().then(function (t) { throw new Error("Server returned " + r.status + ": " + t.slice(0, 100)); });
        }
        return r.json();
      })
      .then(function (data) {
        if (loadingEl) { loadingEl.remove(); loadingEl = null; }
        if (data.error) {
          addBlock("Out [" + cellNum + "]:", data.error, true);
        } else {
          addBlock("Out [" + cellNum + "]:", data.reply);
          tutor_history.push({ role: "user", content: q });
          tutor_history.push({ role: "assistant", content: data.reply });
          if (tutor_history.length > 10) tutor_history = tutor_history.slice(-10);
        }
        cellNum++;
      })
      .catch(function (err) {
        if (loadingEl) { loadingEl.remove(); loadingEl = null; }
        addBlock("Out [" + cellNum + "]:", "Request failed: " + err.message, true);
      })
      .finally(function () {
        send.disabled = false;
      });
  }

  window.openTutorBar = function (cellContent) {
    focusedCell = cellContent;
    if (!panel.classList.contains("open")) toggle();
    input.focus();
  };

  send.addEventListener("click", ask);
  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      ask();
    }
  });
})();
