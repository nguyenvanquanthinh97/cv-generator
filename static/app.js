const state = {
  name: "", headline: "", location: "", email: "", phone: "", website: "", photo: "",
  social_networks: [], summary: "", experience: [], education: [],
  skills: [], certifications: [], theme: "classic",
};

const $ = (id) => document.getElementById(id);
const statusEl = $("status");
const logEl = $("renderLog");

function setStatus(text) {
  statusEl.textContent = text;
  if (text) setTimeout(() => { if (statusEl.textContent === text) statusEl.textContent = ""; }, 2500);
}

async function loadCv() {
  const res = await fetch("/api/cv");
  const data = await res.json();
  Object.assign(state, data);
  renderAll();
}

function renderAll() {
  $("f_name").value = state.name || "";
  $("f_headline").value = state.headline || "";
  $("f_location").value = state.location || "";
  $("f_email").value = state.email || "";
  $("f_phone").value = state.phone || "";
  $("f_website").value = state.website || "";
  $("f_summary").value = state.summary || "";
  $("f_theme").value = state.theme || "classic";
  renderPhoto();

  renderList("social_list", "tpl_social", state.social_networks);
  renderList("experience_list", "tpl_experience", state.experience, true);
  renderList("education_list", "tpl_education", state.education, true);
  renderList("skills_list", "tpl_skills", state.skills);
  renderList("certifications_list", "tpl_certifications", state.certifications, true);
}

function renderList(containerId, templateId, items, hasHighlights) {
  const container = $(containerId);
  container.innerHTML = "";
  items.forEach((item, idx) => {
    const node = $(templateId).content.firstElementChild.cloneNode(true);
    node.dataset.index = idx;
    node.querySelectorAll("[data-field]").forEach((field) => {
      const key = field.dataset.field;
      if (key === "highlights") {
        field.value = (item.highlights || []).join("\n");
      } else {
        field.value = item[key] || "";
      }
    });
    container.appendChild(node);
  });
}

function collectFromDom() {
  state.name = $("f_name").value.trim();
  state.headline = $("f_headline").value.trim();
  state.location = $("f_location").value.trim();
  state.email = $("f_email").value.trim();
  state.phone = $("f_phone").value.trim();
  state.website = $("f_website").value.trim();
  state.summary = $("f_summary").value;
  state.theme = $("f_theme").value;

  state.social_networks = collectRows("social_list", ["network", "username"]);
  state.experience = collectRows("experience_list", ["company", "position", "summary", "location", "start_date", "end_date"], true);
  state.education = collectRows("education_list", ["institution", "area", "degree", "start_date", "end_date"], true);
  state.skills = collectRows("skills_list", ["label", "details"]);
  state.certifications = collectRows("certifications_list", ["name", "url", "date"]);
}

function collectRows(containerId, fields, hasHighlights) {
  const rows = [...$(containerId).querySelectorAll("[data-row]")];
  return rows.map((row) => {
    const obj = {};
    fields.forEach((f) => {
      obj[f] = row.querySelector(`[data-field="${f}"]`).value.trim();
    });
    if (hasHighlights) {
      const raw = row.querySelector('[data-field="highlights"]').value;
      obj.highlights = raw.split("\n").map((l) => l.trim()).filter(Boolean);
    }
    return obj;
  });
}

document.querySelectorAll("[data-add]").forEach((btn) => {
  btn.addEventListener("click", () => {
    collectFromDom();
    const key = btn.dataset.add;
    const blank = {
      social: { network: "LinkedIn", username: "" },
      experience: { company: "", position: "", summary: "", location: "", start_date: "", end_date: "", highlights: [] },
      education: { institution: "", area: "", degree: "", start_date: "", end_date: "", highlights: [] },
      skills: { label: "", details: "" },
      certifications: { name: "", url: "", date: "" },
    }[key];
    const stateKey = key === "social" ? "social_networks" : key;
    state[stateKey].push(blank);
    renderAll();
  });
});

document.addEventListener("click", (e) => {
  if (e.target.matches("[data-remove]")) {
    collectFromDom();
    const row = e.target.closest("[data-row]");
    const container = row.parentElement;
    const idx = [...container.children].indexOf(row);
    const containerId = container.id;
    const keyMap = {
      social_list: "social_networks",
      experience_list: "experience",
      education_list: "education",
      skills_list: "skills",
      certifications_list: "certifications",
    };
    state[keyMap[containerId]].splice(idx, 1);
    renderAll();
  }
});

$("saveBtn").addEventListener("click", async () => {
  collectFromDom();
  setStatus("Saving...");
  const res = await fetch("/api/cv", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(state),
  });
  setStatus(res.ok ? "Saved" : "Save failed");
});

$("renderBtn").addEventListener("click", async () => {
  collectFromDom();
  setStatus("Rendering...");
  logEl.textContent = "";
  const res = await fetch("/api/render", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(state),
  });
  const data = await res.json();
  setStatus(data.ok ? "Rendered" : "Render failed");
  logEl.textContent = data.ok ? "" : data.log;
  if (data.pdf_ready) {
    showPreview();
  }
});

async function showPreview() {
  const container = $("preview_pages");
  container.innerHTML = "";
  let page = 1;
  while (page <= 10) {
    const url = `/api/preview/${page}?t=${Date.now()}`;
    const ok = await new Promise((resolve) => {
      const img = new Image();
      img.onload = () => resolve(true);
      img.onerror = () => resolve(false);
      img.src = url;
    });
    if (!ok) break;
    const img = document.createElement("img");
    img.src = url;
    container.appendChild(img);
    page += 1;
  }
  if (page === 1) {
    container.innerHTML = '<p class="hint">Preview not available.</p>';
  }
}

function renderPhoto() {
  const img = $("photo_preview");
  const removeBtn = $("photo_remove");
  if (state.photo) {
    img.src = `/api/photo?t=${Date.now()}`;
    img.hidden = false;
    removeBtn.hidden = false;
  } else {
    img.hidden = true;
    removeBtn.hidden = true;
  }
}

$("f_photo_input").addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  setStatus("Uploading photo...");
  const formData = new FormData();
  formData.append("photo", file);
  const res = await fetch("/api/photo", { method: "POST", body: formData });
  const data = await res.json();
  e.target.value = "";
  if (res.ok) {
    state.photo = data.photo;
    renderPhoto();
    setStatus("Photo uploaded");
  } else {
    setStatus(data.error || "Upload failed");
  }
});

$("photo_remove").addEventListener("click", async () => {
  setStatus("Removing photo...");
  const res = await fetch("/api/photo", { method: "DELETE" });
  if (res.ok) {
    state.photo = "";
    renderPhoto();
    setStatus("Photo removed");
  } else {
    setStatus("Remove failed");
  }
});

loadCv();
