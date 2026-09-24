// Point this at your running backend (see backend/app.py)
const API_BASE = "http://localhost:8000";

const fileInput = document.getElementById('fileInput');
const pasteArea = document.getElementById('pasteArea');
const fname = document.getElementById('fname');
const parseBtn = document.getElementById('parseBtn');
const resultsCard = document.getElementById('resultsCard');
const segTable = document.getElementById('segTable');
const summaryCard = document.getElementById('summaryCard');
const summaryBody = document.getElementById('summaryBody');

fileInput.addEventListener('change', async () => {
  const f = fileInput.files[0];
  if (!f) return;
  fname.textContent = f.name;
  pasteArea.value = await f.text();
});

function renderSegments(segments) {
  segTable.innerHTML = segments.map(s =>
    `<tr><td class="seg-id">${s.id}</td><td class="seg-meaning">${s.meaning}</td></tr>`
  ).join('');
  resultsCard.classList.remove('hidden');
}

async function callBackend(rawText) {
  const res = await fetch(`${API_BASE}/api/summarize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ raw_text: rawText }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Server error (${res.status})`);
  }
  return res.json();
}

parseBtn.addEventListener('click', async () => {
  const raw = pasteArea.value.trim();
  if (!raw) { alert('Upload a file or paste EDI text first.'); return; }

  parseBtn.disabled = true;
  parseBtn.textContent = 'Working...';
  summaryCard.classList.remove('hidden');
  summaryBody.innerHTML = '<span class="loading">Parsing and asking Claude...</span>';

  try {
    const data = await callBackend(raw);
    renderSegments(data.segments);
    summaryBody.textContent = data.summary;
  } catch (err) {
    summaryBody.innerHTML = `<span class="errbox">${err.message}</span>`;
  } finally {
    parseBtn.disabled = false;
    parseBtn.textContent = 'Parse & Summarize';
  }
});
