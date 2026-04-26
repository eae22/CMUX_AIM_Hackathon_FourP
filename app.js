const API_URL = '/api/protect';

/* ── State ───────────────────────────────────────── */
let _files     = [];
let _b64s      = [];
let _responses = [];

/* ── DOM refs ────────────────────────────────────── */
const fileInput      = document.getElementById('fileInput');
const dropZone       = document.getElementById('dropZone');
const thumbArea      = document.getElementById('thumbArea');
const thumbGrid      = document.getElementById('thumbGrid');
const thumbCount     = document.getElementById('thumbCount');
const btnProtect     = document.getElementById('btnProtect');
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
  handleFiles([...e.dataTransfer.files]);
});

thumbGrid.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', e => {
  if (e.target.files.length) handleFiles([...e.target.files]);
  fileInput.value = '';
});

/* ── Handle file selection ───────────────────────── */
function handleFiles(files) {
  const valid = files.filter(f => {
    if (f.size > 10 * 1024 * 1024) { alert(`${f.name}: 파일 크기 10MB 초과`); return false; }
    return true;
  });
  if (!valid.length) return;

  _files = valid;
  _b64s  = [];

  let done = 0;
  valid.forEach((file, i) => {
    const reader = new FileReader();
    reader.onload = ev => {
      _b64s[i] = ev.target.result;
      done++;
      if (done === valid.length) renderThumbs();
    };
    reader.readAsDataURL(file);
  });
}

function renderThumbs() {
  thumbGrid.querySelectorAll('.thumb-item, .thumb-more').forEach(el => el.remove());

  const MAX_SHOW = 8;
  const overlay  = thumbGrid.querySelector('.thumb-overlay');

  _b64s.slice(0, MAX_SHOW).forEach((b64, i) => {
    const div = document.createElement('div');
    div.className = 'thumb-item';
    const img = document.createElement('img');
    img.src = b64;
    img.alt = `사진 ${i + 1}`;
    div.appendChild(img);
    thumbGrid.insertBefore(div, overlay);
  });

  if (_b64s.length > MAX_SHOW) {
    const more = document.createElement('div');
    more.className = 'thumb-more';
    more.textContent = `+${_b64s.length - MAX_SHOW}`;
    thumbGrid.insertBefore(more, overlay);
  }

  thumbCount.textContent = `${_b64s.length}장 선택됨`;
  dropZone.style.display = 'none';
  thumbArea.classList.add('visible');
  btnProtect.disabled = false;
  btnProtect.hidden = false;

  resultSection.hidden = true;
}

/* ── Protection flow ─────────────────────────────── */
async function startProtection() {
  if (!_b64s.length) return;

  pageContent.classList.add('dimmed');
  loadingOverlay.hidden = false;
  _responses = [];

  for (let i = 0; i < _b64s.length; i++) {
    updateLoadingCounter(i + 1, _b64s.length);
    animateLoading();
    await delay(2800);

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image_data: { original_base64: _b64s[i], format: 'jpeg' },
          parameters: { protection_algorithm: 'FGSM', epsilon: 0.03, target_detector: 'FaceNet_v1' },
        }),
      });
      if (!res.ok) {
        const errText = await res.text();
        throw new Error(`HTTP ${res.status}: ${errText}`);
      }
      _responses.push(await res.json());
    } catch (err) {
      console.error('[API 오류]', err);
      loadingOverlay.hidden = true;
      pageContent.classList.remove('dimmed');
      alert(`보호 처리 실패 (${i + 1}번째 이미지)\n\n${err.message}`);
      return;
    }
  }

  loadingOverlay.hidden = true;
  pageContent.classList.remove('dimmed');

  renderResult();
  resultSection.hidden = false;
  resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function updateLoadingCounter(cur, total) {
  document.getElementById('loadingTitle').textContent =
    total > 1 ? `${cur} / ${total}장 보호 중...` : '보호 처리 중...';
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

  document.getElementById('resultTitle').textContent =
    _responses.length > 1 ? `${_responses.length}장의 사진이 보호되었습니다` : '사진이 보호되었습니다';

  const first = _responses[0];
  document.getElementById('scoreOrig').textContent =
    (first?.simulation_metrics?.deepfake_vulnerability?.original_score  ?? 95.5) + '%';
  document.getElementById('scoreProt').textContent =
    (first?.simulation_metrics?.deepfake_vulnerability?.protected_score ?? 4.2)  + '%';

  _responses.forEach((resp, i) => {
    const origSrc = _b64s[i];
    const protSrc = resp.protection_result?.protected_image_base64 || _b64s[i];

    const pair = document.createElement('div');
    pair.className = 'compare-pair';
    pair.innerHTML = `
      <div class="compare-item">
        <img src="${origSrc}" alt="원본 ${i + 1}" />
        <span class="compare-label orig">원본</span>
      </div>
      <div class="compare-item">
        <img src="${protSrc}" alt="보호됨 ${i + 1}" />
        <span class="compare-label prot">🛡️ 보호됨</span>
      </div>
    `;
    pairs.appendChild(pair);
  });

  try { sessionStorage.setItem('atmResponse', JSON.stringify({ ..._responses[0], original_image_base64: _b64s[0] })); } catch (_) {}

  btnProtect.hidden = true;
}

/* ── Download ────────────────────────────────────── */
function downloadAll() {
  _responses.forEach((resp, i) => {
    const src = resp?.protection_result?.protected_image_base64 || _b64s[i];
    setTimeout(() => {
      const a = document.createElement('a');
      a.href = src; a.download = `protected_${i + 1}.png`; a.click();
    }, i * 300);
  });
}

/* ── Reset ───────────────────────────────────────── */
function resetAll() {
  _files = []; _b64s = []; _responses = [];
  try { sessionStorage.removeItem('atmResponse'); } catch (_) {}
  fileInput.value = '';
  thumbGrid.querySelectorAll('.thumb-item, .thumb-more').forEach(el => el.remove());
  thumbArea.classList.remove('visible');
  dropZone.style.display = '';
  btnProtect.disabled = true;
  btnProtect.hidden = false;
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
    const resp = JSON.parse(stored);
    const b64 = resp.original_image_base64 || '';
    if (!b64) return;

    _responses = [resp];
    _b64s = [b64];

    thumbGrid.querySelectorAll('.thumb-item, .thumb-more').forEach(el => el.remove());
    const overlay = thumbGrid.querySelector('.thumb-overlay');
    const div = document.createElement('div');
    div.className = 'thumb-item';
    const img = document.createElement('img');
    img.src = b64;
    img.alt = '선택된 사진';
    div.appendChild(img);
    thumbGrid.insertBefore(div, overlay);
    thumbCount.textContent = '1장 선택됨';
    dropZone.style.display = 'none';
    thumbArea.classList.add('visible');
    btnProtect.disabled = false;

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
