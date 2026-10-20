"use strict";

(() => {
  const storageKey = "codefactory.todo.v1";
  const form = document.getElementById("task-form");
  const input = document.getElementById("task-input");
  const error = document.getElementById("input-error");
  const warning = document.getElementById("storage-warning");
  const list = document.getElementById("task-list");
  const count = document.getElementById("task-count");
  const empty = document.getElementById("empty-state");
  const help = document.getElementById("list-help");
  const announcement = document.getElementById("announcement");
  let tasks = [];

  function showWarning(message) {
    warning.textContent = message;
    warning.hidden = false;
  }

  try {
    const saved = localStorage.getItem(storageKey);
    if (saved !== null) {
      const parsed = JSON.parse(saved);
      const ids = new Set();
      if (!Array.isArray(parsed) || !parsed.every(task => {
        if (!task || typeof task.id !== "string" || !task.id || ids.has(task.id)
            || typeof task.text !== "string" || !task.text.trim()
            || typeof task.completed !== "boolean") return false;
        ids.add(task.id);
        return true;
      })) throw new Error("Dados inválidos");
      tasks = parsed.map(({ id, text, completed }) => ({ id, text, completed }));
    }
  } catch {
    showWarning("Não foi possível recuperar a lista salva. Você pode usar uma nova lista; se o armazenamento estiver indisponível, as alterações podem ser perdidas ao fechar ou recarregar a página.");
  }

  function save() {
    try {
      localStorage.setItem(storageKey, JSON.stringify(tasks));
      warning.hidden = true;
      warning.textContent = "";
    } catch {
      showWarning("Não foi possível salvar neste navegador. Você pode continuar usando a lista, mas as alterações podem ser perdidas ao fechar ou recarregar a página.");
    }
  }

  function updateSummary() {
    const completed = tasks.filter(task => task.completed).length;
    const pending = tasks.length - completed;
    count.textContent = tasks.length
      ? `${pending} ${pending === 1 ? "pendente" : "pendentes"} · ${completed} ${completed === 1 ? "concluída" : "concluídas"}`
      : "Nenhuma tarefa";
    empty.hidden = tasks.length > 0;
    help.hidden = tasks.length === 0;
  }

  function makeTask(task) {
    const row = document.createElement("li");
    row.className = task.completed ? "task completed" : "task";
    const label = document.createElement("label");
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = task.completed;
    const text = document.createElement("span");
    text.className = "task-text";
    text.textContent = task.text;
    label.append(checkbox, text);

    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "delete-button";
    remove.setAttribute("aria-label", `Excluir tarefa: ${task.text}`);
    remove.title = "Excluir tarefa";
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("fill", "none");
    svg.setAttribute("stroke", "currentColor");
    svg.setAttribute("stroke-width", "1.7");
    svg.setAttribute("stroke-linecap", "round");
    svg.setAttribute("stroke-linejoin", "round");
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", "M4 6h16M9 6V3h6v3M6 6l1 15h10l1-15M10 10v7M14 10v7");
    svg.append(path);
    remove.append(svg);

    checkbox.addEventListener("change", () => {
      task.completed = checkbox.checked;
      row.classList.toggle("completed", task.completed);
      save();
      updateSummary();
      announcement.textContent = task.completed ? "Tarefa concluída." : "Tarefa reaberta.";
    });
    remove.addEventListener("click", () => {
      const restoreFocus = row.contains(document.activeElement);
      const nextFocus = row.nextElementSibling?.querySelector("input")
        || row.previousElementSibling?.querySelector("input") || input;
      tasks = tasks.filter(item => item.id !== task.id);
      row.remove();
      save();
      updateSummary();
      if (restoreFocus) nextFocus.focus();
      announcement.textContent = "Tarefa excluída.";
    });
    row.append(label, remove);
    return row;
  }

  form.addEventListener("submit", event => {
    event.preventDefault();
    const text = input.value.trim();
    if (!text) {
      error.textContent = "Escreva uma tarefa antes de adicionar.";
      error.hidden = false;
      input.setAttribute("aria-invalid", "true");
      input.focus();
      return;
    }
    let id;
    do {
      id = globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random()}`;
    } while (tasks.some(task => task.id === id));
    const task = { id, text, completed: false };
    tasks.push(task);
    list.append(makeTask(task));
    save();
    updateSummary();
    input.value = "";
    error.hidden = true;
    input.removeAttribute("aria-invalid");
    input.focus();
    announcement.textContent = "Tarefa adicionada.";
  });

  input.addEventListener("input", () => {
    error.hidden = true;
    input.removeAttribute("aria-invalid");
  });

  tasks.forEach(task => list.append(makeTask(task)));
  updateSummary();
})();
