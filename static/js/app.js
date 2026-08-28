let currentSession = null;

const messagesEl = document.querySelector("#messages");
const sessionsEl = document.querySelector("#sessions");
const input = document.querySelector("#messageInput");
const frame = document.querySelector("#artifactFrame");
const artifactEmpty = document.querySelector("#artifactEmpty");
const sendBtn = document.querySelector("#sendBtn");
const artifactPane = document.querySelector("#artifactPane");
const artifactToggle = document.querySelector("#artifactToggle");
const artifactClose = document.querySelector("#artifactClose");

/* ---------- click ripple on every button ---------- */
document.addEventListener("pointerdown", (e) => {
  const btn = e.target.closest("button");
  if (!btn) return;
  const rect = btn.getBoundingClientRect();
  const size = Math.max(rect.width, rect.height) * 1.6;
  const ripple = document.createElement("span");
  ripple.className = "ripple";
  ripple.style.width = ripple.style.height = `${size}px`;
  ripple.style.left = `${e.clientX - rect.left - size / 2}px`;
  ripple.style.top = `${e.clientY - rect.top - size / 2}px`;
  btn.appendChild(ripple);
  ripple.addEventListener("animationend", () => ripple.remove());
});

/* ---------- textarea auto-grow ---------- */
function autoGrow() {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 160) + "px";
}
input.addEventListener("input", autoGrow);
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    document.querySelector("#chatForm").requestSubmit();
  }
});

async function api(path, options = {}) {
  const res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}

function avatarSVG(role) {
  if (role === "assistant") {
    return `<svg viewBox="0 0 24 24"><rect x="3" y="9" width="3" height="6" rx="1.5" fill="currentColor"/><rect x="10.5" y="4" width="3" height="16" rx="1.5" fill="currentColor"/><rect x="18" y="9" width="3" height="6" rx="1.5" fill="currentColor"/></svg>`;
  }
  return `<svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4" fill="currentColor"/><path d="M4 20c0-4.4 3.6-7 8-7s8 2.6 8 7" fill="currentColor"/></svg>`;
}

function escapeHTML(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function stripArtifact(content) {
  return content.replace(/<artifact[\s\S]*?<\/artifact>/g, "").trim();
}

function formatInline(value) {
  return escapeHTML(value)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*\n]+)\*/g, "<em>$1</em>");
}

function isTableDivider(line) {
  return /^\s*\|?[\s:-]+\|[\s|:-]+\|?\s*$/.test(line);
}

function renderTable(lines, startIndex) {
  if (!lines[startIndex]?.includes("|") || !isTableDivider(lines[startIndex + 1] || "")) return null;
  const rows = [];
  let i = startIndex;
  while (i < lines.length && lines[i].includes("|") && lines[i].trim()) {
    if (!isTableDivider(lines[i])) {
      rows.push(lines[i].trim().replace(/^\||\|$/g, "").split("|").map(cell => cell.trim()));
    }
    i += 1;
  }
  if (!rows.length) return null;
  const [head, ...body] = rows;
  const thead = `<thead><tr>${head.map(cell => `<th>${formatInline(cell)}</th>`).join("")}</tr></thead>`;
  const tbody = `<tbody>${body.map(row => `<tr>${row.map(cell => `<td>${formatInline(cell)}</td>`).join("")}</tr>`).join("")}</tbody>`;
  return { html: `<div class="md-table-wrap"><table>${thead}${tbody}</table></div>`, nextIndex: i };
}

function renderMarkdown(markdown) {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  const html = [];
  let listType = null;

  function closeList() {
    if (!listType) return;
    html.push(`</${listType}>`);
    listType = null;
  }

  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i];
    const trimmed = line.trim();
    if (!trimmed) {
      closeList();
      continue;
    }

    const table = renderTable(lines, i);
    if (table) {
      closeList();
      html.push(table.html);
      i = table.nextIndex - 1;
      continue;
    }

    const heading = trimmed.match(/^(#{1,4})\s+(.+)$/);
    if (heading) {
      closeList();
      const level = Math.min(heading[1].length + 1, 4);
      html.push(`<h${level}>${formatInline(heading[2])}</h${level}>`);
      continue;
    }

    const quote = trimmed.match(/^>\s+(.+)$/);
    if (quote) {
      closeList();
      html.push(`<blockquote>${formatInline(quote[1])}</blockquote>`);
      continue;
    }

    const bullet = trimmed.match(/^[-*]\s+(.+)$/);
    if (bullet) {
      if (listType !== "ul") {
        closeList();
        listType = "ul";
        html.push("<ul>");
      }
      html.push(`<li>${formatInline(bullet[1])}</li>`);
      continue;
    }

    const numbered = trimmed.match(/^\d+[.)]\s+(.+)$/);
    if (numbered) {
      if (listType !== "ol") {
        closeList();
        listType = "ol";
        html.push("<ol>");
      }
      html.push(`<li>${formatInline(numbered[1])}</li>`);
      continue;
    }

    closeList();
    html.push(`<p>${formatInline(trimmed)}</p>`);
  }
  closeList();
  return html.join("");
}

function renderMessage(role, content, citations = []) {
  const el = document.createElement("article");
  el.className = `message ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.innerHTML = avatarSVG(role);
  el.appendChild(avatar);

  const body = document.createElement("div");
  body.className = "msg-body";

  const text = document.createElement("div");
  const visibleContent = stripArtifact(content);
  text.className = role === "assistant" ? "markdown" : "plain-message";
  text.innerHTML = role === "assistant" ? renderMarkdown(visibleContent) : escapeHTML(visibleContent);
  body.appendChild(text);

  if (role === "assistant" && citations.length) {
    const note = document.createElement("div");
    note.className = "source-note";
    note.textContent = `Answered from Lenny transcript evidence (${citations.length} sources).`;
    body.appendChild(note);
  }

  if (role === "assistant") {
    const copyBtn = document.createElement("button");
    copyBtn.className = "copy-btn";
    copyBtn.type = "button";
    copyBtn.textContent = "Copy";
    copyBtn.onclick = async () => {
      await navigator.clipboard.writeText(visibleContent);
      copyBtn.textContent = "Copied";
      copyBtn.classList.add("copied");
      setTimeout(() => { copyBtn.textContent = "Copy"; copyBtn.classList.remove("copied"); }, 1400);
    };
    body.appendChild(copyBtn);
  }

  el.appendChild(body);
  messagesEl.appendChild(el);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return el;
}

function showThinking() {
  const el = document.createElement("article");
  el.className = "message assistant loading-message";
  el.innerHTML = `
    <div class="avatar">${avatarSVG("assistant")}</div>
    <div class="msg-body">
      <div class="thinking"><span></span><span></span><span></span><span></span></div>
    </div>`;
  messagesEl.appendChild(el);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return el;
}

async function loadSessions() {
  const data = await api("/api/sessions");
  sessionsEl.innerHTML = "";
  data.forEach((s, i) => {
    const row = document.createElement("div");
    row.className = "session-row" + (s.id === currentSession ? " is-active" : "");
    row.style.animationDelay = `${i * 30}ms`;

    const btn = document.createElement("button");
    btn.className = "session";
    btn.type = "button";
    btn.textContent = s.title;
    btn.onclick = () => openSession(s.id);

    const del = document.createElement("button");
    del.className = "delete-session";
    del.type = "button";
    del.setAttribute("aria-label", "Delete session");
    del.textContent = "x";
    del.onclick = async (event) => {
      event.stopPropagation();
      del.disabled = true;
      row.remove();
      await api(`/api/sessions/${s.id}`, { method: "DELETE" });
      if (s.id === currentSession) {
        currentSession = null;
        messagesEl.innerHTML = "";
        setArtifact(null);
        renderMessage("assistant", "Session deleted. Start a new conversation when you're ready.");
        await loadSessions();
      } else {
        await loadSessions();
      }
    };

    row.appendChild(btn);
    row.appendChild(del);
    sessionsEl.appendChild(row);
  });
}

function setArtifact(content, options = {}) {
  if (!content) {
    frame.classList.remove("is-loaded");
    artifactEmpty.classList.remove("is-hidden");
    artifactToggle.disabled = true;
    artifactToggle.textContent = "No artifact";
    artifactPane.classList.remove("is-open");
    artifactPane.setAttribute("aria-hidden", "true");
    return;
  }
  artifactToggle.disabled = false;
  artifactToggle.textContent = "View artifact";
  artifactEmpty.classList.add("is-hidden");
  frame.classList.remove("is-loaded");
  frame.srcdoc = content;
  frame.onload = () => frame.classList.add("is-loaded");
  if (options.open) {
    artifactPane.classList.add("is-open");
    artifactPane.setAttribute("aria-hidden", "false");
  }
}

artifactToggle.onclick = () => {
  if (artifactToggle.disabled) return;
  artifactPane.classList.add("is-open");
  artifactPane.setAttribute("aria-hidden", "false");
};

artifactClose.onclick = () => {
  artifactPane.classList.remove("is-open");
  artifactPane.setAttribute("aria-hidden", "true");
};

async function openSession(id) {
  currentSession = id;
  const data = await api(`/api/sessions/${id}`);
  messagesEl.innerHTML = "";
  setArtifact(null);
  data.messages.forEach(m => renderMessage(m.role, m.content, m.citations));
  await loadSessions();
}

async function newSession() {
  const data = await api("/api/sessions", { method: "POST", body: "{}" });
  currentSession = data.id;
  document.querySelector("#provider").textContent = `provider: ${data.provider}`;
  messagesEl.innerHTML = "";
  setArtifact(null);
  renderMessage("assistant", "Ask me about Lenny's Podcast. I'll ground answers in the transcripts and show sources.");
  await loadSessions();
}

document.querySelector("#newSession").onclick = newSession;
document.querySelector("#chatForm").onsubmit = async (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  if (!currentSession) await newSession();

  input.value = "";
  autoGrow();
  renderMessage("user", text);
  const loading = showThinking();
  sendBtn.disabled = true;
  sendBtn.classList.add("is-sending");

  try {
    const result = await api("/api/chat/message", { method: "POST", body: JSON.stringify({ session_id: currentSession, message: text }) });
    loading.remove();
    renderMessage("assistant", result.answer, result.citations);
    if (result.artifact) {
      setArtifact(result.artifact.content, { open: true });
      artifactToggle.textContent = "View artifact";
    }
  } catch (err) {
    loading.querySelector(".msg-body").innerHTML = `<span class="error-text">${escapeHTML(err.message)}</span>`;
  } finally {
    sendBtn.disabled = false;
    sendBtn.classList.remove("is-sending");
    input.focus();
  }
};

api("/api/health").then(h => document.querySelector("#provider").textContent = `provider: ${h.provider}`);
loadSessions().then(() => newSession());
