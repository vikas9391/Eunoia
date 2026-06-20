// 🎤 Speech to text
document.addEventListener("DOMContentLoaded", function () {
  const micBtn = document.getElementById("micBtn");
  if (window.SpeechRecognition || window.webkitSpeechRecognition) {
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = "en-US";
    micBtn.onclick = () => recognition.start();
    recognition.onresult = (event) => {
      document.getElementById("user-input").value = event.results[0][0].transcript;
    };
  } else {
    micBtn.disabled = true;
    micBtn.title = "Speech recognition not supported";
  }
});

// 💬 Typing effect
function typeEffect(element, text) {
  let i = 0;
  function typing() {
    if (i < text.length) {
      element.innerHTML += text.charAt(i);
      i++;
      setTimeout(typing, 20);
      scrollToBottom();
    }
  }
  typing();
}

// 🔽 Keep chat scrolled down
function scrollToBottom() {
  const chatBox = document.getElementById("chat-box");
  if (chatBox) chatBox.scrollTop = chatBox.scrollHeight;
}

let currentSessionId = null;

// 🚀 Send message with loader + typewriter
async function sendMessage() {
  const input = document.getElementById("user-input");
  const msg = input.value.trim();
  if (!msg || !currentSessionId) return;

  const chatBox = document.getElementById("chat-box");

  // ✅ Add user message
  chatBox.innerHTML += `<div class="bubble user"><b> </b> ${msg}</div>`;
  scrollToBottom();
  input.value = "";
  input.disabled = true;

  // ✅ Add Bot typing dots
  const loaderDiv = document.createElement("div");
  loaderDiv.className = "bubble assistant";
  loaderDiv.innerHTML = `
    <b> </b>
    <div class="typing-indicator">
      <span></span><span></span><span></span>
    </div>
  `;
  chatBox.appendChild(loaderDiv);
  scrollToBottom();

  try {
    const response = await fetch("/chatbot/api/chat/send/", {
      method: "POST",
      headers: { 
        "Content-Type": "application/json", 
        "X-CSRFToken": getCookie("csrftoken") 
      },
      body: JSON.stringify({ message: msg, session_id: currentSessionId })
    });

    const data = await response.json();
    const botReply = data.response || data.error || "No response.";

    // ✅ Replace dots with typewriter reply
    loaderDiv.innerHTML = "<b> </b> ";
    typeEffect(loaderDiv, botReply);

  } catch (err) {
    console.error("❌ Error:", err);
    loaderDiv.innerHTML = "<b> </b> ⚠️ Error loading response";
    showCustomAlert("❌ Error sending message: " + err.message, "Error", true);
  } finally {
    input.disabled = false;
    input.focus();
    loadHistory();
  }
}

// 📜 Load chat sessions (sidebar)
async function loadHistory() {
  try {
    const res = await fetch("/chatbot/api/chat/sessions/");
    if (!res.ok) {
      showCustomAlert("❌ Failed to fetch sessions: " + res.statusText, "Error", true);
      return;
    }
    const { sessions } = await res.json();
    const list = document.getElementById("history-list");
    list.innerHTML = "";

    sessions.forEach(session => {
      const li = document.createElement("li");
      li.classList.add("chat-session");
      li.dataset.id = session.session_id;

      // Generate session title like ChatGPT
      let sessionName = "New Chat"; // fallback
      if (session.title && session.title.trim() !== "") {
        sessionName = session.title;
      } else if (session.messages && session.messages.length > 0) {
        const firstMsg = session.messages[0].content.trim();
        sessionName = firstMsg.length > 30 ? firstMsg.slice(0, 30) + "..." : firstMsg;
      }

      li.innerHTML = `
        <span class="chat-title">${sessionName}</span>
        <input class="rename-input hidden" type="text" />
        <div class="chat-actions">
          <button class="menu-btn">⋮</button>
          <div class="dropdown-menu hidden">
            <button class="rename-btn">✏️ Rename</button>
            <button class="clear-btn">🗑️ Clear History</button>
            <button class="delete-btn">❌ Delete</button>
          </div>
        </div>
      `;

      // Click on session title
      li.querySelector(".chat-title").onclick = () => loadChat(session.session_id);

      // Highlight active session
      if (currentSessionId == session.session_id) li.classList.add("active");

      // Add dropdown toggle
      const menuBtn = li.querySelector(".menu-btn");
      const dropdown = li.querySelector(".dropdown-menu");

      menuBtn.addEventListener("click", (e) => {
        e.stopPropagation(); // prevent closing immediately
        dropdown.classList.toggle("hidden");
      });

      list.appendChild(li);
    });

    // Close any open dropdown if clicking outside
    document.addEventListener("click", () => {
      document.querySelectorAll(".dropdown-menu").forEach(dd => dd.classList.add("hidden"));
    });

  } catch (err) {
    console.error("⚠️ Error loading history:", err);
    showCustomAlert("⚠️ Error loading chat history: " + err.message, "Error", true);
  }
}



// 📜 Load full chat by session id
async function loadChat(sessionId) {
  try {
    const res = await fetch(`/chatbot/api/chat/messages/${sessionId}/`);
    if (!res.ok) {
      showCustomAlert(`❌ Failed to fetch chat ${sessionId}: ${res.statusText}`, "Error", true);
      return;
    }
    const { conversation } = await res.json();
    const chatBox = document.getElementById("chat-box");
    chatBox.innerHTML = "";
    currentSessionId = sessionId;
    for (const msg of conversation) {
      const div = document.createElement("div");
      div.className = "bubble " + (msg.role === "user" ? "user" : "assistant");
      div.innerHTML = `<b>${msg.role === "user" ? "You" : "Bot"}:</b> `;
      chatBox.appendChild(div);
      typeEffect(div, msg.text);
    }
    scrollToBottom();
  } catch (err) {
    console.error(`⚠️ Error loading chat ${sessionId}:`, err);
    showCustomAlert(`⚠️ Error loading chat: ${err.message}`, "Error", true);
  }
}

// ➕ Start a new chat session
async function startNewChat() {
  try {
    const res = await fetch("/chatbot/api/chat/new/", {
      method: "POST",
      headers: { "X-CSRFToken": getCookie("csrftoken") }
    });
    const data = await res.json();
    if (data.session_id) {
      currentSessionId = data.session_id;
      document.getElementById("chat-box").innerHTML = "";
      loadHistory();
    }
  } catch (err) {
    showCustomAlert("❌ Error starting new chat: " + err.message, "Error", true);
  }
}

// 📌 Toggle sidebar
function toggleSidebar() {
  const sidebar = document.getElementById("sidebar");
  const container = document.getElementById("main-container");
  const button = document.getElementById("toggle-btn");

  sidebar.classList.toggle("closed");
  container.classList.toggle("full");

  // Hide button when sidebar is open
  if (!sidebar.classList.contains("closed")) {
    button.style.display = "none"; // hide
  } else {
    button.style.display = "block"; // show again
  }
}

// CSRF helper (Django)
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.substring(0, name.length + 1) === (name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Load sidebar + start a new chat on first load if none
window.onload = async function () {
  await loadHistory();
  if (!currentSessionId) await startNewChat();
};

// ⌨️ Send on Enter, newline on Shift+Enter
document.addEventListener("DOMContentLoaded", function () {
  const userInput = document.getElementById("user-input");
  userInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
});

document.addEventListener("click", (event) => {
  // Toggle menu
  if (event.target.classList.contains("menu-btn")) {
    const menu = event.target.nextElementSibling;
    menu.classList.toggle("hidden");
  }

  // Inline rename
  if (event.target.classList.contains("rename-btn")) {
    const li = event.target.closest(".chat-session");
    const titleSpan = li.querySelector(".chat-title");
    const input = li.querySelector(".rename-input");

    titleSpan.classList.add("hidden");
    input.classList.remove("hidden");
    input.value = titleSpan.textContent.trim();
    input.focus();

    const saveRename = async () => {
      const sessionId = li.dataset.id;
      const newName = input.value.trim();
      if (newName) {
        await fetch(`/chatbot/api/chat/session/${sessionId}/rename/`, {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
          },
          body: JSON.stringify({ title: newName }),
        });
        titleSpan.textContent = newName;
      }
      input.classList.add("hidden");
      titleSpan.classList.remove("hidden");
      input.removeEventListener("keydown", handler); // cleanup
    };

    const handler = (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        saveRename();
      }
      if (e.key === "Escape") {
        input.classList.add("hidden");
        titleSpan.classList.remove("hidden");
        input.removeEventListener("keydown", handler);
      }
    };
    input.addEventListener("keydown", handler);
  }

  // Clear history
  if (event.target.classList.contains("clear-btn")) {
    const li = event.target.closest(".chat-session");
    const sessionId = li.dataset.id;

    // Custom confirm (see instructions below to wire this up)
    customConfirm("Clear all messages in this session?", "Confirm Clear", (confirmed) => {
      if (confirmed) {
        fetch(`/chatbot/api/chat/session/${sessionId}/clear/`, {
          method: "DELETE",
          headers: { "X-CSRFToken": getCookie("csrftoken") },
        })
        .then(res => {
          if (!res.ok) throw new Error("Failed to clear session history");

          // ✅ If current session → clear chat box immediately
          if (currentSessionId == sessionId) {
            document.getElementById("chat-box").innerHTML = "";
          }

          // ✅ Refresh sidebar so latest session order updates
          loadHistory();
        })
        .catch(err => {
          showCustomAlert("❌ Error clearing history: " + err.message, "Error", true);
        });
      }
    });
  }

  // Delete session
  if (event.target.classList.contains("delete-btn")) {
    const li = event.target.closest(".chat-session");
    const sessionId = li.dataset.id;

    // Custom confirm (see instructions below to wire this up)
    customConfirm("Delete this session?", "Confirm Delete", (confirmed) => {
      if (confirmed) {
        fetch(`/chatbot/api/chat/session/${sessionId}/delete/`, {
          method: "DELETE",
          headers: { "X-CSRFToken": getCookie("csrftoken") },
        })
        .then(res => {
          if (!res.ok) throw new Error("Failed to delete session");
          li.remove();

          // ✅ If current session was deleted → reset everything
          if (currentSessionId == sessionId) {
            currentSessionId = null;
            document.getElementById("chat-box").innerHTML = ""; // clear old chat
            startNewChat().then(loadHistory);
          } else {
            loadHistory();
          }
        })
        .catch(err => {
          showCustomAlert("❌ Error deleting session: " + err.message, "Error", true);
        });
      }
    });
  }
});

const sidebar = document.getElementById("sidebar");
const container = document.getElementById("main-container");
const toggleBtn = document.getElementById("toggle-btn");
const closeBtn = document.getElementById("close-sidebar");

// Open sidebar
toggleBtn.addEventListener("click", () => {
  sidebar.classList.remove("closed");
  container.classList.remove("full");
  toggleBtn.style.display = "none"; // hide ☰
});

// Close sidebar
closeBtn.addEventListener("click", () => {
  sidebar.classList.add("closed");
  container.classList.add("full");
  toggleBtn.style.display = "block"; // show ☰
});

// Custom alert popup functions
function showCustomAlert(msg, title = "Message", isError = false) {
  document.getElementById("custom-alert-msg").textContent = msg;
  document.getElementById("custom-alert-title").textContent = title;
  document.getElementById("custom-alert").style.display = "flex";
  document.getElementById("custom-alert-icon").style.display = isError ? "block" : "none";
}

function closeCustomAlert() {
  document.getElementById("custom-alert").style.display = "none";
}

// Custom confirm popup function
function customConfirm(message, title = "Confirm", callback) {
  const confirmBackdrop = document.getElementById("custom-confirm");
  document.getElementById("custom-confirm-title").textContent = title;
  document.getElementById("custom-confirm-msg").textContent = message;
  confirmBackdrop.style.display = "flex";
  const yesBtn = document.getElementById("custom-confirm-yes");
  const noBtn = document.getElementById("custom-confirm-no");

  // Remove previous listeners
  yesBtn.onclick = null;
  noBtn.onclick = null;

  yesBtn.onclick = function () {
    confirmBackdrop.style.display = "none";
    callback(true);
  };
  noBtn.onclick = function () {
    confirmBackdrop.style.display = "none";
    callback(false);
  };
}

