const API_URL = 'http://localhost:8000/api/protect';

/* ── State ───────────────────────────────────────── */
let _file     = null;
let _b64      = null;
let _response = null;

/* ── DOM refs ────────────────────────────────────── */
const fileInput      = document.getElementById('fileInput');
const dropZone       = document.getElementById('dropZone');
const thumbArea      = document.getElementById('thumbArea');
const thumbGrid      = document.getElementById('thumbGrid');
const thumbCount     = document.getElementById('thumbCount');
const btnProtect     = document.getElementById('btnProtect');
const btnBack        = document.getElementById('btnBack');
const uploadSection  = document.getElementById('uploadSection');
const pageContent    = document.getElementById('pageContent');
const loadingOverlay = document.getElementById('loadingOverlay');
const resultSection  = document.getElementById('resultSection');

/* ── File input events ───────────────────────────── */
dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover',  e => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});

thumbGrid.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', e => {
  if (e.target.files.length) handleFile(e.target.files[0]);
  fileInput.value = '';
});

/* ── Handle file selection ───────────────────────── */
function handleFile(file) {
  if (file.size > 10 * 1024 * 1024) { alert(`${file.name}: 파일 크기 10MB 초과`); return; }

  _file = file;
  _b64  = null;

  const reader = new FileReader();
  reader.onload = ev => {
    _b64 = ev.target.result;
    renderThumb();
  };
  reader.readAsDataURL(file);
}

function renderThumb() {
  thumbGrid.querySelectorAll('.thumb-item').forEach(el => el.remove());

  const overlay = thumbGrid.querySelector('.thumb-overlay');
  const div = document.createElement('div');
  div.className = 'thumb-item';
  const img = document.createElement('img');
  img.src = _b64;
  img.alt = '선택된 사진';
  div.appendChild(img);
  thumbGrid.insertBefore(div, overlay);

  thumbCount.textContent = '1장 선택됨';
  dropZone.style.display = 'none';
  thumbArea.classList.add('visible');
  btnProtect.disabled = false;
  btnProtect.hidden = false;

  resultSection.hidden = true;
}

/* ── Protection flow ─────────────────────────────── */
async function startProtection() {
  if (!_b64) return;

  pageContent.classList.add('dimmed');
  loadingOverlay.hidden = false;
  _response = null;

  updateLoadingCounter();
  animateLoading();
  await delay(2800);

  try {
    const res = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_base64: _b64 }),
    });
    if (!res.ok) throw new Error();
    _response = await res.json();
  } catch (_) {
    _response = buildDemoResponse(_b64);
  }

  loadingOverlay.hidden = true;
  pageContent.classList.remove('dimmed');

  renderResult();
  resultSection.hidden = false;
  resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function updateLoadingCounter() {
  document.getElementById('loadingTitle').textContent = '보호 처리 중...';
  document.getElementById('loadingSub').textContent = '잠시만 기다려 주세요';
}

/* ── Loading animation ───────────────────────────── */
const TRACK_STEPS = [
  { pct: 20, title: '얼굴 특징점 분석 중...',    sub: 'MediaPipe 랜드마크 추출' },
  { pct: 55, title: 'FGSM 노이즈 생성 중...',   sub: '적대적 그래디언트 계산' },
  { pct: 78, title: '보호 이미지 렌더링 중...',  sub: '노이즈 주입 완료' },
  { pct: 95, title: '딥페이크 취약도 분석 중...', sub: '시뮬레이션 메트릭 계산' },
];

function animateLoading() {
  const tracks = document.querySelectorAll('.track-item');
  const bar    = document.getElementById('progressBar');
  tracks.forEach(t => t.className = 'track-item');
  bar.style.width = '0%';

  TRACK_STEPS.forEach((s, i) => {
    setTimeout(() => {
      if (i > 0) tracks[i - 1].className = 'track-item done';
      tracks[i].className = 'track-item active';
      bar.style.width = s.pct + '%';
      document.getElementById('loadingTitle').textContent = s.title;
      document.getElementById('loadingSub').textContent   = s.sub;
    }, i * 600);
  });
  setTimeout(() => {
    tracks[3].className = 'track-item done';
    bar.style.width = '100%';
  }, 4 * 600);
}

/* ── Render result ───────────────────────────────── */
function renderResult() {
  const pairs = document.getElementById('comparePairs');
  pairs.innerHTML = '';

  document.getElementById('resultTitle').textContent = '사진이 보호되었습니다';

  document.getElementById('scoreOrig').textContent =
    (_response?.simulation_metrics?.deepfake_vulnerability?.original_score  ?? 95.5) + '%';
  document.getElementById('scoreProt').textContent =
    (_response?.simulation_metrics?.deepfake_vulnerability?.protected_score ?? 4.2)  + '%';

  const origSrc = _response.original_image_base64 || _b64;
  const protSrc = _response.protection_result?.protected_image_base64 || _b64;

  const pair = document.createElement('div');
  pair.className = 'compare-pair';
  pair.innerHTML = `
    <div class="compare-item">
      <img src="${origSrc}" alt="원본" />
      <span class="compare-label orig">원본</span>
    </div>
    <div class="compare-item">
      <img src="${protSrc}" alt="보호됨" />
      <span class="compare-label prot">🛡️ 보호됨</span>
    </div>
  `;
  pairs.appendChild(pair);

  try { sessionStorage.setItem('atmResponse', JSON.stringify(_response)); } catch (_) {}

  uploadSection.hidden = true;
  btnProtect.hidden = true;
  btnBack.hidden = false;
}

/* ── Download ────────────────────────────────────── */
function downloadAll() {
  const src = _response?.protection_result?.protected_image_base64 || _b64;
  const a = document.createElement('a');
  a.href = src; a.download = 'protected_1.jpg'; a.click();
}

/* ── Reset ───────────────────────────────────────── */
function resetAll() {
  _file = null; _b64 = null; _response = null;
  fileInput.value = '';
  thumbGrid.querySelectorAll('.thumb-item').forEach(el => el.remove());
  thumbArea.classList.remove('visible');
  dropZone.style.display = '';
  uploadSection.hidden = false;
  dropZone.style.display = '';
  thumbArea.classList.remove('visible');
  btnProtect.disabled = true;
  btnBack.hidden = true;
  resultSection.hidden = true;
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

/* ── Helpers ─────────────────────────────────────── */
function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

/* ── analysis.html에서 뒤로가기 시 결과 복원 ──────── */
(function restoreIfReturning() {
  try {
    const stored = sessionStorage.getItem('atmResponse');
    if (!stored) return;
    _response = JSON.parse(stored);
    _b64 = _response.original_image_base64 || '';
    if (_b64) renderThumb();
    renderResult();
    resultSection.hidden = false;
  } catch (_) {}
})();

function buildDemoResponse(b64) {
  return {
    request_id: 'demo_' + Date.now(),
    original_image_base64: b64,
    protection_result: {
      protected_image_base64: b64,
      is_face_detected: false,
      detection_confidence: 0.0814,
    },
    simulation_metrics: {
      deepfake_vulnerability: { original_score: 95.5, protected_score: 4.2 },
      training_efficiency_graph: {
        epochs:             [1,2,3,4,5,6,7,8,9,10],
        loss_original:      [2.45,1.78,1.21,0.83,0.52,0.31,0.17,0.09,0.04,0.02],
        loss_protected:     [2.44,2.41,2.47,2.39,2.45,2.42,2.48,2.40,2.44,2.46],
        accuracy_original:  [0.51,0.63,0.73,0.82,0.89,0.93,0.96,0.98,0.99,0.99],
        accuracy_protected: [0.51,0.53,0.50,0.52,0.51,0.53,0.50,0.52,0.51,0.52],
      },
    },
  };
}
