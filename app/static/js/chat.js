(() => {
  if (location.pathname === "/login") {
    try { localStorage.removeItem("token"); } catch (_) {}
    return;
  }

  if (window.__authChecked) return;
  window.__authChecked = true;

  let username = null;
  let ws = null;
  let reconnectTimer = null;

  const chatBox       = document.getElementById("chat-box");
  const chatForm      = document.getElementById("chat-form");
  const messageInput  = document.getElementById("message");
  const userInfo      = document.getElementById("user-info");
  const logoutBtn     = document.getElementById("logout-btn");
  const chatContainer = document.querySelector(".chat-container");
  const header        = document.querySelector(".header");

  function hideChatUI() {
    if (header)        header.style.display = "none";
    if (chatContainer) chatContainer.style.display = "none";
    if (chatForm)      chatForm.style.display = "none";
  }
  function showChatUI() {
    if (header)        header.style.display = "";
    if (chatContainer) chatContainer.style.display = "";
    if (chatForm)      chatForm.style.display = "";
  }
  hideChatUI();

  if (logoutBtn) {
    logoutBtn.onclick = () => {
      localStorage.removeItem("token");
      window.location.href = "/login";
    };
  }

  function onAuth(usernameStr) {
    username = usernameStr;
    if (userInfo) userInfo.innerText = username;
    if (logoutBtn) logoutBtn.style.display = "inline-block";
    showChatUI();
    connectWs();
  }

  tryAuth();

  async function tryAuth() {
    const token = localStorage.getItem("token");
    if (!token) { window.location.href = "/login"; return; }

    try {
      const res = await fetch("/me", { headers: { "Authorization": "Bearer " + token } });
      if (res.ok) {
        const data = await res.json();
        onAuth(data.username);
      } else {
        localStorage.removeItem("token");
        window.location.href = "/login";
      }
    } catch {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
  }

  function loadHistory() {
    const token = localStorage.getItem("token");
    if (!token || !chatBox) return;

    fetch("/messages", { headers: { "Authorization": "Bearer " + token } })
      .then(res => res.json())
      .then(messages => {
        chatBox.innerHTML = "";
        messages.forEach(appendMessage);
      })
      .catch(() => {});
  }

  function connectWs() {
    const token = localStorage.getItem("token");
    if (!token) return;

    try { ws && ws.close(); } catch {}

    const url =
      (location.protocol === "https:" ? "wss://" : "ws://") +
      location.host +
      "/ws/chat?token=" + encodeURIComponent(token);

    ws = new WebSocket(url);

    ws.onopen = () => {
      if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null; }
      loadHistory();
    };

    ws.onmessage = event => {
      try { appendMessage(JSON.parse(event.data)); } catch {}
    };

    ws.onclose = () => {
      if (!reconnectTimer) reconnectTimer = setTimeout(connectWs, 1500);
    };

    ws.onerror = () => { try { ws.close(); } catch {} };
  }

  if (chatForm) {
    chatForm.onsubmit = e => {
      e.preventDefault();
      if (!messageInput || !messageInput.value.trim()) return;
      ws?.send(JSON.stringify({ text: messageInput.value }));
      messageInput.value = "";
      messageInput.focus();
    };
  }

  function appendMessage(msg) {
    if (!chatBox) return;

    const msgDiv = document.createElement("div");
    msgDiv.classList.add("message");
    if (msg.username === username) msgDiv.classList.add("own");

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    bubble.innerHTML =
      `<span class="username">${escapeHtml(msg.username)}</span>` +
      `<div class="text">${escapeHtml(msg.text)}</div>` +
      `<div class="timestamp">${msg.timestamp ?? ""}</div>`;

    msgDiv.appendChild(bubble);
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  function escapeHtml(text) {
    return String(text).replace(/[<>&"'`]/g, c => ({
      "<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;", "'": "&#39;", "`": "&#96;"
    })[c]);
  }
})();
(() => {
  if (location.pathname === "/login") {
    try { localStorage.removeItem("token"); } catch (_) {}
    return;
  }

  if (window.__authChecked) return;
  window.__authChecked = true;

  let username = null;
  let ws = null;
  let reconnectTimer = null;

  const chatBox       = document.getElementById("chat-box");
  const chatForm      = document.getElementById("chat-form");
  const messageInput  = document.getElementById("message");
  const userInfo      = document.getElementById("user-info");
  const logoutBtn     = document.getElementById("logout-btn");
  const chatContainer = document.querySelector(".chat-container");
  const header        = document.querySelector(".header");

  function hideChatUI() {
    if (header)        header.style.display = "none";
    if (chatContainer) chatContainer.style.display = "none";
    if (chatForm)      chatForm.style.display = "none";
  }
  function showChatUI() {
    if (header)        header.style.display = "";
    if (chatContainer) chatContainer.style.display = "";
    if (chatForm)      chatForm.style.display = "";
  }
  hideChatUI();

  if (logoutBtn) {
    logoutBtn.onclick = () => {
      localStorage.removeItem("token");
      window.location.href = "/login";
    };
  }

  function onAuth(usernameStr) {
    username = usernameStr;
    if (userInfo) userInfo.innerText = username;
    if (logoutBtn) logoutBtn.style.display = "inline-block";
    showChatUI();
    connectWs();
  }

  tryAuth();

  async function tryAuth() {
    const token = localStorage.getItem("token");
    if (!token) { window.location.href = "/login"; return; }

    try {
      const res = await fetch("/me", { headers: { "Authorization": "Bearer " + token } });
      if (res.ok) {
        const data = await res.json();
        onAuth(data.username);
      } else {
        localStorage.removeItem("token");
        window.location.href = "/login";
      }
    } catch {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
  }

  function loadHistory() {
    const token = localStorage.getItem("token");
    if (!token || !chatBox) return;

    fetch("/messages", { headers: { "Authorization": "Bearer " + token } })
      .then(res => res.json())
      .then(messages => {
        chatBox.innerHTML = "";
        messages.forEach(appendMessage);
      })
      .catch(() => {});
  }

  function connectWs() {
    const token = localStorage.getItem("token");
    if (!token) return;

    try { ws && ws.close(); } catch {}

    const url =
      (location.protocol === "https:" ? "wss://" : "ws://") +
      location.host +
      "/ws/chat?token=" + encodeURIComponent(token);

    ws = new WebSocket(url);

    ws.onopen = () => {
      if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null; }
      loadHistory();
    };

    ws.onmessage = event => {
      try { appendMessage(JSON.parse(event.data)); } catch {}
    };

    ws.onclose = () => {
      if (!reconnectTimer) reconnectTimer = setTimeout(connectWs, 1500);
    };

    ws.onerror = () => { try { ws.close(); } catch {} };
  }

  if (chatForm) {
    chatForm.onsubmit = e => {
      e.preventDefault();
      if (!messageInput || !messageInput.value.trim()) return;
      ws?.send(JSON.stringify({ text: messageInput.value }));
      messageInput.value = "";
      messageInput.focus();
    };
  }

  function appendMessage(msg) {
    if (!chatBox) return;

    const msgDiv = document.createElement("div");
    msgDiv.classList.add("message");
    if (msg.username === username) msgDiv.classList.add("own");

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    bubble.innerHTML =
      `<span class="username">${escapeHtml(msg.username)}</span>` +
      `<div class="text">${escapeHtml(msg.text)}</div>` +
      `<div class="timestamp">${msg.timestamp ?? ""}</div>`;

    msgDiv.appendChild(bubble);
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  function escapeHtml(text) {
    return String(text).replace(/[<>&"'`]/g, c => ({
      "<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;", "'": "&#39;", "`": "&#96;"
    })[c]);
  }
})();
