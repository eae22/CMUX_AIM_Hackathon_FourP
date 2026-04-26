/* ─── 더미 데이터 (백엔드 연결 전 기본값) ─── */
const RESULT_DATA = {
  level: "safe",
  protectionScore: 92,

  similarityBefore: 99,
  similarityAfter:  8,

  photo: {
    originalSrc:  "",
    protectedSrc: "",
  },

  heatmapSrc: "",

  deepfakeVulnerability: {
    original_score:  95.5,
    protected_score: 4.2,
  },

  trainingGraph: {
    epochs:             [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    loss_original:      [2.45, 1.78, 1.21, 0.83, 0.52, 0.31, 0.17, 0.09, 0.04, 0.02],
    loss_protected:     [2.44, 2.41, 2.47, 2.39, 2.45, 2.42, 2.48, 2.40, 2.44, 2.46],
    accuracy_original:  [0.51, 0.63, 0.73, 0.82, 0.89, 0.93, 0.96, 0.98, 0.99, 0.99],
    accuracy_protected: [0.51, 0.53, 0.50, 0.52, 0.51, 0.53, 0.50, 0.52, 0.51, 0.52],
  },

  analyzedAt:     "2026-04-26 · 14:32",
  customHeadline: null,
  customDesc:     null
};

const API_BASE_URL = "http://localhost:8000";

const LEVEL_CONFIG = {
  safe: {
    label: "안전",
    icon:  "✦",
    color: "var(--safe)",
    dim:   "var(--safe-dim)",
    headline: score => `사진이 ${score}% 보호되어 있어요`,
    desc:  "이 사진으로 딥페이크를 만들기 매우 어렵습니다. 지금 바로 안심하고 공유하세요.",
    tags:  ["공유 가능", "딥페이크 차단됨"]
  },
  warn: {
    label: "주의",
    icon:  "⚠",
    color: "var(--warn)",
    dim:   "var(--warn-dim)",
    headline: score => `사진이 ${score}% 보호되어 있어요`,
    desc:  "어느 정도 보호되어 있지만 완벽하지 않아요. 중요한 사진이라면 재처리 후 사용하세요.",
    tags:  ["신중하게 공유", "재처리 권장"]
  },
  danger: {
    label: "경고",
    icon:  "✕",
    color: "var(--danger)",
    dim:   "var(--danger-dim)",
    headline: score => `보호 강도가 ${score}%로 낮아요`,
    desc:  "지금 상태로 공유하면 딥페이크에 악용될 수 있어요. 재처리 후 사용하세요.",
    tags:  ["공유 보류 권장", "재처리 필요"]
  }
};

/* ════════════════════════
   State
   ════════════════════════ */
let _currentData      = RESULT_DATA;
let _currentRequestId = null;

/* ════════════════════════
   Init — index.html이 sessionStorage에 저장한 응답 우선 사용
   ════════════════════════ */
(function init() {
  try {
    const stored = sessionStorage.getItem('atmResponse');
    if (stored) {
      const resp      = JSON.parse(stored);
      const detBefore = Math.round((resp.original_analysis?.detection_confidence ?? 0.99) * 100);
      const detAfter  = Math.round((resp.protection_result?.detection_confidence  ?? 0.08) * 100);
      const protScore = Math.round((1 - (resp.protection_result?.detection_confidence ?? 0.08)) * 100);
      _currentRequestId = resp.request_id || null;

      renderResult({
        level:            protScore >= 70 ? 'safe' : protScore >= 40 ? 'warn' : 'danger',
        protectionScore:  protScore,
        similarityBefore: detBefore,
        similarityAfter:  detAfter,
        photo: {
          originalSrc:  resp.original_image_base64  || '',
          protectedSrc: resp.protection_result?.protected_image_base64 || '',
        },
        heatmapSrc:            resp.original_analysis?.ai_perception?.grad_cam_heatmap || '',
        trainingGraph:         resp.simulation_metrics?.training_efficiency_graph      || RESULT_DATA.trainingGraph,
        deepfakeVulnerability: resp.simulation_metrics?.deepfake_vulnerability         || RESULT_DATA.deepfakeVulnerability,
        analyzedAt:    new Date().toLocaleString('ko-KR'),
        customHeadline: null,
        customDesc:     null,
      });
      return;
    }
  } catch (_) {}

  renderResult(RESULT_DATA);
})();

/* ─── helpers ─── */
function showSlot(slot, src) {
  const img = document.getElementById('img-' + slot);
  const ph  = document.getElementById('ph-'  + slot);
  img.src = src;
  img.style.display = 'block';
  ph.style.display  = 'none';
}

function animateNumber(el, from, to, duration) {
  const start = performance.now();
  function step(now) {
    const t = Math.min((now - start) / duration, 1);
    const ease = 1 - Math.pow(1 - t, 4);
    el.textContent = Math.round(from + (to - from) * ease);
    if (t < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

/* ─── renderResult: 데이터 객체로 전체 UI 갱신 ─── */
function renderResult(d) {
  _currentData = d;
  const cfg    = LEVEL_CONFIG[d.level];
  const clr    = cfg.color;
  const circum = 2 * Math.PI * 48;

  document.getElementById('analyzed-at').textContent = d.analyzedAt;

  if (d.photo.originalSrc)  showSlot('original',  d.photo.originalSrc);
  if (d.photo.protectedSrc) showSlot('protected', d.photo.protectedSrc);

  const badge = document.getElementById('status-badge');
  badge.style.background = cfg.dim;
  badge.style.color = clr;
  badge.style.border = `1px solid ${clr}40`;
  document.getElementById('badge-icon').textContent  = cfg.icon;
  document.getElementById('badge-label').textContent = cfg.label;

  document.getElementById('status-title').textContent =
    d.level === 'safe' ? '보호 상태 양호' :
    d.level === 'warn' ? '보호 수준 보통' : '보호 수준 낮음';

  const redEl = document.getElementById('stat-reduction');
  redEl.textContent = `−${d.similarityBefore - d.similarityAfter}%p`;
  redEl.style.color = clr;

  const gaugeFill = document.getElementById('gauge-fill');
  const pctEl     = document.getElementById('gauge-pct');
  gaugeFill.style.stroke = clr;
  pctEl.style.color = clr;
  gaugeFill.style.transition = 'none';
  gaugeFill.style.strokeDashoffset = circum;
  pctEl.textContent = '0';
  setTimeout(() => {
    gaugeFill.style.transition = 'stroke-dashoffset 1.4s cubic-bezier(0.22, 1, 0.36, 1)';
    gaugeFill.style.strokeDashoffset = circum - (circum * d.protectionScore / 100);
    animateNumber(pctEl, 0, d.protectionScore, 1400);
  }, 80);

  document.getElementById('bar-pct-before').textContent = d.similarityBefore + '%';
  document.getElementById('bar-pct-after').textContent  = d.similarityAfter  + '%';
  const bB = document.getElementById('bar-before');
  const bA = document.getElementById('bar-after');
  bB.style.transition = bA.style.transition = 'none';
  bB.style.width = bA.style.width = '0%';
  setTimeout(() => {
    bB.style.transition = bA.style.transition = 'width 1.2s cubic-bezier(0.22, 1, 0.36, 1)';
    bB.style.width = d.similarityBefore + '%';
    bA.style.width = d.similarityAfter  + '%';
  }, 200);

  document.getElementById('ai-headline').textContent = d.customHeadline || cfg.headline(d.protectionScore);
  document.getElementById('ai-desc').textContent     = d.customDesc     || cfg.desc;
  const tagsEl = document.getElementById('ai-tags');
  tagsEl.innerHTML = '';
  cfg.tags.forEach(t => {
    const span = document.createElement('span');
    span.className = 'ai-tag';
    span.textContent = '#' + t;
    tagsEl.appendChild(span);
  });

  const hmImg = document.getElementById('img-heatmap');
  const hmPh  = document.getElementById('ph-heatmap');
  if (d.heatmapSrc) {
    hmImg.src = d.heatmapSrc;
    hmImg.style.display = 'block';
    hmPh.style.display  = 'none';
  } else {
    hmImg.style.display = 'none';
    hmPh.style.display  = 'flex';
  }

  if (d.trainingGraph) {
    setTimeout(() => {
      const g       = d.trainingGraph;
      const lossMax = Math.ceil(Math.max(...g.loss_original, ...g.loss_protected) * 2) / 2;
      drawChart('chart-loss', g.epochs, g.loss_original,     g.loss_protected,     lossMax);
      drawChart('chart-acc',  g.epochs, g.accuracy_original, g.accuracy_protected, 1.0);
    }, 100);
    renderTrainingDesc(d.trainingGraph, d.deepfakeVulnerability);
  }
}

/* ─── renderTrainingDesc: 차트 아래 동적 설명 ─── */
function renderTrainingDesc(tg, vuln) {
  if (!tg) return;
  const avg = arr => arr.reduce((a, b) => a + b, 0) / arr.length;
  const f   = n   => Number(n).toFixed(1);

  const lossFirst   = tg.loss_original[0];
  const lossLast    = tg.loss_original[tg.loss_original.length - 1];
  const lossProtAvg = avg(tg.loss_protected);
  const lossReduct  = ((lossFirst - lossLast) / lossFirst * 100);

  const accOrigLast = tg.accuracy_original[tg.accuracy_original.length - 1] * 100;
  const accProtAvg  = avg(tg.accuracy_protected) * 100;

  const lossEl = document.getElementById('desc-loss');
  const accEl  = document.getElementById('desc-acc');

  if (lossEl) lossEl.innerHTML =
    `<strong>Loss</strong> — 원본은 ${f(lossFirst)}에서 ${f(lossLast)}로 ` +
    `<strong>${f(lossReduct)}%</strong> 감소했어요. ` +
    `보호본은 ${f(lossProtAvg)} 수준을 유지해 학습이 거의 진행되지 않았습니다.`;

  let accText =
    `<strong>Accuracy</strong> — 원본 학습 정확도가 <strong>${f(accOrigLast)}%</strong>까지 올랐지만, ` +
    `보호본은 ${f(accProtAvg)}% 수준에 머물렀어요.`;
  if (vuln) {
    accText +=
      ` 딥페이크 취약도도 ${f(vuln.original_score)}에서 <strong>${f(vuln.protected_score)}</strong>으로 낮아졌습니다.`;
  }
  if (accEl) accEl.innerHTML = accText;
}

/* ─── drawChart: canvas 라인 차트 ─── */
function drawChart(id, epochs, line1, line2, yMax) {
  const canvas = document.getElementById(id);
  if (!canvas) return;
  const wrap = canvas.parentElement;
  canvas.width  = wrap.clientWidth  || 360;
  canvas.height = wrap.clientHeight || 100;
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  const p = { t: 8, r: 10, b: 20, l: 28 };
  const cW = W - p.l - p.r, cH = H - p.t - p.b;

  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = '#242424';
  ctx.fillRect(0, 0, W, H);

  ctx.strokeStyle = '#2a2a2a';
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = p.t + (cH / 4) * i;
    ctx.beginPath(); ctx.moveTo(p.l, y); ctx.lineTo(p.l + cW, y); ctx.stroke();
    ctx.fillStyle = '#666'; ctx.font = '9px sans-serif'; ctx.textAlign = 'right';
    ctx.fillText((yMax * (4 - i) / 4).toFixed(1), p.l - 3, y + 3);
  }

  ctx.fillStyle = '#666'; ctx.font = '9px sans-serif'; ctx.textAlign = 'center';
  [0, Math.floor((epochs.length - 1) / 2), epochs.length - 1].forEach(i => {
    const x = p.l + (cW / (epochs.length - 1)) * i;
    ctx.fillText(epochs[i], x, H - 4);
  });

  function line(data, color) {
    ctx.beginPath(); ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.lineJoin = 'round';
    data.forEach((v, i) => {
      const x = p.l + (cW / (data.length - 1)) * i;
      const y = p.t + cH - Math.min(v / yMax, 1) * cH;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.stroke();
  }
  line(line1, '#ef4444');
  line(line2, '#22c55e');
}

/* ─── fetchProtection: 백엔드 직접 호출 시 사용 ─── */
async function fetchProtection(imageB64) {
  setLoading(true);
  try {
    const res = await fetch(`${API_BASE_URL}/analyze`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        image_data: { original_base64: imageB64 },
        parameters: { protection_algorithm: 'FGSM', epsilon: 0.03 }
      })
    });
    if (!res.ok) throw new Error(`서버 오류 ${res.status}`);
    const data = await res.json();

    _currentRequestId = data.request_id;

    const detBefore      = Math.round(data.original_analysis.detection_confidence * 100);
    const detAfter       = Math.round(data.protection_result.detection_confidence * 100);
    const protectedScore = Math.round((1 - data.protection_result.detection_confidence) * 100);

    renderResult({
      level:            protectedScore >= 70 ? 'safe' : protectedScore >= 40 ? 'warn' : 'danger',
      protectionScore:  protectedScore,
      similarityBefore: detBefore,
      similarityAfter:  detAfter,
      photo: {
        originalSrc:  imageB64,
        protectedSrc: data.protection_result.protected_image_base64,
      },
      heatmapSrc:            data.original_analysis.ai_perception.grad_cam_heatmap,
      trainingGraph:         data.simulation_metrics.training_efficiency_graph,
      deepfakeVulnerability: data.simulation_metrics.deepfake_vulnerability,
      analyzedAt:            new Date().toLocaleString('ko-KR'),
      customHeadline: null,
      customDesc:     null,
    });
    setLoading(false);
  } catch (err) {
    setLoading(false, err.message);
  }
}

function setLoading(on, errMsg) {
  const hint = document.querySelector('.compare-hint');
  if (on) {
    if (hint) hint.innerHTML = '<span class="loading-spinner"></span> 분석 중…';
  } else if (errMsg) {
    if (hint) hint.textContent = `⚠ 연결 실패: ${errMsg}`;
  } else {
    if (hint) hint.textContent = '';
  }
}

async function downloadProtected() {
  if (!_currentRequestId) return;
  const res  = await fetch(`${API_BASE_URL}/api/download/${_currentRequestId}`);
  const blob = await res.blob();
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = 'shieldface_protected.png';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

async function shareResult() {
  const btn      = document.querySelector('.btn-primary');
  const origText = btn.textContent;
  btn.textContent = '캡처 중…';
  btn.disabled    = true;

  try {
    const canvas = await html2canvas(document.getElementById('app'), {
      backgroundColor: '#0a0a0a',
      scale: 2,
      useCORS: true,
      logging: false,
    });

    canvas.toBlob(async blob => {
      const score = _currentData.protectionScore;
      const shareText = `내 사진이 ${score}% 보호되었습니다! #FaceNotFound #딥페이크차단`;
      const file = new File([blob], 'shieldface-result.png', { type: 'image/png' });

      // 모바일: 이미지 파일 포함 네이티브 공유
      if (navigator.canShare && navigator.canShare({ files: [file] })) {
        try {
          await navigator.share({ title: 'FaceNotFound 결과', text: shareText, files: [file] });
          btn.textContent = origText;
          btn.disabled = false;
          return;
        } catch (_) {}
      }

      // 데스크톱 / 폴백: PNG 다운로드
      const url = URL.createObjectURL(blob);
      const a   = document.createElement('a');
      a.href     = url;
      a.download = 'shieldface-result.png';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      btn.textContent = '저장됨!';
      setTimeout(() => { btn.textContent = origText; btn.disabled = false; }, 1800);
    }, 'image/png');

  } catch (_) {
    // html2canvas 실패 시 텍스트 복사로 폴백
    const text = `내 사진이 ${_currentData.protectionScore}% 보호되었습니다! #FaceNotFound #딥페이크차단`;
    try { await navigator.clipboard.writeText(text); } catch (__) {}
    btn.textContent = '복사됨!';
    setTimeout(() => { btn.textContent = origText; btn.disabled = false; }, 1800);
  }
}
