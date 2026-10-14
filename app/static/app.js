"use strict";

const $ = (sel) => document.querySelector(sel);
const state = { meta: null, appointments: [], editingId: null, deletingId: null };

/* ---------- helpers ---------- */

// Escape text before putting it in innerHTML so patient names can never inject markup.
function esc(value) {
  const div = document.createElement("div");
  div.textContent = value;
  return div.innerHTML;
}

function formatWhen(iso) {
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    weekday: "short", day: "numeric", month: "short", year: "numeric",
    hour: "numeric", minute: "2-digit",
  });
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (res.status === 204) return null;
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(body.error || "Something went wrong.");
    err.fields = body.fields || {};
    throw err;
  }
  return body;
}

function showBanner(message) {
  const el = $("#banner");
  el.textContent = message;
  el.hidden = !message;
}

function fillSelect(select, options, placeholder) {
  select.innerHTML = (placeholder ? `<option value="">${esc(placeholder)}</option>` : "") +
    options.map((o) => `<option>${esc(o)}</option>`).join("");
}

/* ---------- list + filters ---------- */

function currentQuery() {
  const params = new URLSearchParams();
  const map = { search: "#f-search", doctor: "#f-doctor", type: "#f-type",
                status: "#f-status", date_from: "#f-from", date_to: "#f-to" };
  for (const [key, sel] of Object.entries(map)) {
    const value = $(sel).value.trim();
    if (value) params.set(key, value);
  }
  return params.toString();
}

function hasActiveFilter() {
  return currentQuery() !== "";
}

async function loadAppointments() {
  try {
    showBanner("");
    state.appointments = await api(`/api/appointments?${currentQuery()}`);
    renderRows();
  } catch (err) {
    showBanner(`Could not load appointments. ${err.message}`);
  }
}

function renderRows() {
  const rows = state.appointments;
  $("#rows").innerHTML = rows.map((a) => `
    <tr>
      <td class="when">${esc(formatWhen(a.appointment_time))}</td>
      <td>${esc(a.patient_name)}</td>
      <td>${esc(a.doctor)}</td>
      <td>${esc(a.appointment_type)}</td>
      <td><span class="status ${esc(a.status)}">${esc(a.status)}</span></td>
      <td class="actions-cell">
        <button class="btn small" data-action="edit" data-id="${a.id}" aria-label="Edit appointment for ${esc(a.patient_name)}">Edit</button>
        <button class="btn small" data-action="delete" data-id="${a.id}" aria-label="Delete appointment for ${esc(a.patient_name)}">Delete</button>
      </td>
    </tr>`).join("");

  $("#count").textContent = `${rows.length} appointment${rows.length === 1 ? "" : "s"} shown`;
  const empty = $("#empty");
  empty.hidden = rows.length > 0;
  empty.textContent = hasActiveFilter()
    ? "No appointments match these filters. Try clearing one."
    : "No appointments yet. Select New appointment to add the first one.";
}

/* ---------- create / edit ---------- */

function clearErrors() {
  document.querySelectorAll(".field-error").forEach((el) => (el.textContent = ""));
}

function openForm(appointment) {
  clearErrors();
  const form = $("#form");
  form.reset();
  state.editingId = appointment ? appointment.id : null;
  $("#form-title").textContent = appointment ? "Edit appointment" : "New appointment";
  if (appointment) {
    for (const [key, value] of Object.entries(appointment)) {
      if (form.elements[key]) form.elements[key].value = value;
    }
  } else {
    form.elements.status.value = "Scheduled";
  }
  $("#form-dialog").showModal();
}

async function submitForm(event) {
  event.preventDefault();
  clearErrors();
  const form = $("#form");
  const data = Object.fromEntries(new FormData(form).entries());

  // Light client-side check; the server is the real authority.
  let ok = true;
  for (const key of ["patient_name", "appointment_time", "doctor", "appointment_type"]) {
    if (!String(data[key] || "").trim()) {
      document.querySelector(`[data-for="${key}"]`).textContent = "This field is required.";
      ok = false;
    }
  }
  if (!ok) return;

  try {
    const isEdit = state.editingId !== null;
    await api(isEdit ? `/api/appointments/${state.editingId}` : "/api/appointments", {
      method: isEdit ? "PUT" : "POST",
      body: JSON.stringify(data),
    });
    $("#form-dialog").close();
    await loadAppointments();
  } catch (err) {
    const fields = Object.entries(err.fields || {});
    if (fields.length === 0) $("#form-error").textContent = err.message;
    for (const [key, message] of fields) {
      const el = document.querySelector(`[data-for="${key}"]`);
      if (el) el.textContent = message; else $("#form-error").textContent = message;
    }
  }
}

/* ---------- delete ---------- */

function askDelete(appointment) {
  state.deletingId = appointment.id;
  $("#delete-text").textContent =
    `${appointment.patient_name} with ${appointment.doctor}, ${formatWhen(appointment.appointment_time)}. This cannot be undone.`;
  $("#delete-dialog").showModal();
}

async function confirmDelete() {
  if ($("#delete-dialog").returnValue !== "confirm") return;
  try {
    await api(`/api/appointments/${state.deletingId}`, { method: "DELETE" });
    await loadAppointments();
  } catch (err) {
    showBanner(`Could not delete the appointment. ${err.message}`);
  }
}

/* ---------- wiring ---------- */

function debounce(fn, ms) {
  let timer;
  return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), ms); };
}

async function init() {
  try {
    state.meta = await api("/api/meta");
  } catch (err) {
    showBanner(`Could not start the app. ${err.message}`);
    return;
  }
  const { doctors, types, statuses } = state.meta;
  fillSelect($("#f-doctor"), doctors, "All doctors");
  fillSelect($("#f-type"), types, "All types");
  fillSelect($("#f-status"), statuses, "All statuses");
  fillSelect($("#form").elements.doctor, doctors, "Choose a doctor");
  fillSelect($("#form").elements.appointment_type, types, "Choose a type");
  fillSelect($("#form").elements.status, statuses);

  $("#new-btn").addEventListener("click", () => openForm(null));
  $("#cancel-btn").addEventListener("click", () => $("#form-dialog").close());
  $("#form").addEventListener("submit", submitForm);
  $("#delete-dialog").addEventListener("close", confirmDelete);

  $("#rows").addEventListener("click", (event) => {
    const btn = event.target.closest("button[data-action]");
    if (!btn) return;
    const appt = state.appointments.find((a) => a.id === Number(btn.dataset.id));
    if (!appt) return;
    if (btn.dataset.action === "edit") openForm(appt); else askDelete(appt);
  });

  const reload = debounce(loadAppointments, 250);
  $("#f-search").addEventListener("input", reload);
  for (const sel of ["#f-doctor", "#f-type", "#f-status", "#f-from", "#f-to"]) {
    $(sel).addEventListener("change", loadAppointments);
  }
  $("#clear-btn").addEventListener("click", () => {
    document.querySelectorAll(".filters input, .filters select").forEach((el) => (el.value = ""));
    loadAppointments();
  });

  loadAppointments();
}

init();
