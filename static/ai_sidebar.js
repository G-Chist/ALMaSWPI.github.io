(function () {
  var btn = document.getElementById("ai-sidebar-btn");
  var panel = document.getElementById("ai-sidebar-panel");
  var close = document.getElementById("ai-sidebar-close");
  var msgs = document.getElementById("ai-sidebar-msgs");
  var input = document.getElementById("ai-sidebar-input");
  var send = document.getElementById("ai-sidebar-send");

  function toggle() {
    panel.classList.toggle("open");
    btn.classList.toggle("shifted");
  }

  btn.addEventListener("click", toggle);
  close.addEventListener("click", toggle);

  function addMsg(role, text) {
    var div = document.createElement("div");
    div.className = "msg " + role;
    if (role === "assistant") {
      div.innerHTML = marked.parse(text);
      if (typeof renderMathInElement === "function") {
        renderMathInElement(div, {
          delimiters: [
            { left: "$$", right: "$$", display: true },
            { left: "$", right: "$", display: false },
          ],
        });
      }
    } else {
      div.textContent = text;
    }
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
  }

  var history = [];

  function getPageText() {
    var body = document.body;
    var clone = body.cloneNode(true);
    var exclude = clone.querySelector("#ai-sidebar-wrap");
    if (exclude) exclude.remove();
    var els = clone.querySelectorAll(
      "script,style,nav,header,footer,#spaghettios-banner"
    );
    for (var i = 0; i < els.length; i++) els[i].remove();
    return (clone.textContent || "").trim().slice(0, 8000);
  }

  function ask() {
    var q = input.value.trim();
    if (!q) return;
    input.value = "";
    addMsg("user", q);
    addMsg("loading", "Thinking...");
    send.disabled = true;
    fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: q, context: getPageText(), history: history }),
    })
      .then(function (r) {
        return r.json();
      })
      .then(function (data) {
        var loaders = msgs.querySelectorAll(".msg.loading");
        for (var i = 0; i < loaders.length; i++) loaders[i].remove();
        if (data.error) {
          addMsg("error", data.error);
        } else {
          addMsg("assistant", data.reply);
          history.push({ role: "user", content: q });
          history.push({ role: "assistant", content: data.reply });
          if (history.length > 5) history = history.slice(-5);
        }
      })
      .catch(function (err) {
        var loaders = msgs.querySelectorAll(".msg.loading");
        for (var i = 0; i < loaders.length; i++) loaders[i].remove();
        addMsg("error", "Request failed: " + err.message);
      })
      .finally(function () {
        send.disabled = false;
      });
  }

  send.addEventListener("click", ask);
  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      ask();
    }
  });
})();
