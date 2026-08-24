// ============================================================
// Post Insight Studio - frontend logic
// Plain JavaScript, no framework, no build step.
// A 3-step wizard: Upload -> Read -> Improve.
// ============================================================

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB

const ACCEPTED_TYPES = [
  'application/pdf',
  'image/png',
  'image/jpeg',
  'image/jpg',
  'image/webp'
];

let selectedFile = null;
let processInterval = null;
let selectedPlatform = 'Instagram';


// ============================================================
// PLATFORM
// ============================================================

const platformSelect = document.getElementById('platformSelect');

platformSelect.addEventListener('change', () => {
  selectedPlatform = platformSelect.value;
});


// ============================================================
// SHARED ELEMENT REFERENCES
// ============================================================

const stepNodes = document.querySelectorAll('.step-node');

const panels = {
  1: document.getElementById('panel-1'),
  2: document.getElementById('panel-2'),
  3: document.getElementById('panel-3'),
};


function goToStep(stepNumber) {

  Object.entries(panels).forEach(([num, el]) => {

    el.classList.toggle(
      'active',
      Number(num) === stepNumber
    );

  });


  stepNodes.forEach((node) => {

    const n = Number(node.dataset.step);

    node.classList.toggle(
      'active',
      n === stepNumber
    );

    node.classList.toggle(
      'done',
      n < stepNumber
    );

  });

}


// ============================================================
// STEP 1 — FILE SELECTION
// ============================================================

const dropzone = document.getElementById('dropzone');
const dropzoneText = document.getElementById('dropzoneText');
const fileInput = document.getElementById('fileInput');
const toStep2Btn = document.getElementById('toStep2Btn');
const step1Error = document.getElementById('step1Error');


dropzone.addEventListener('click', () => {
  fileInput.click();
});


dropzone.addEventListener('dragover', (e) => {

  e.preventDefault();

  dropzone.classList.add('dragging');

});


dropzone.addEventListener('dragleave', () => {

  dropzone.classList.remove('dragging');

});


dropzone.addEventListener('drop', (e) => {

  e.preventDefault();

  dropzone.classList.remove('dragging');

  handleFileChosen(
    e.dataTransfer.files[0]
  );

});


fileInput.addEventListener('change', (e) => {

  handleFileChosen(
    e.target.files[0]
  );

});


function handleFileChosen(file) {

  hide(step1Error);

  if (!file) return;


  // ==========================================================
  // FILE TYPE VALIDATION
  // ==========================================================

  if (!ACCEPTED_TYPES.includes(file.type)) {

    showNotice(
      step1Error,
      'Unsupported file type. Please upload a PDF, PNG, JPEG, or WEBP file.'
    );

    selectedFile = null;
    toStep2Btn.disabled = true;

    return;
  }


  // ==========================================================
  // FILE SIZE VALIDATION
  // Maximum allowed file size: 10 MB
  // ==========================================================

  if (file.size > MAX_FILE_SIZE) {

    showNotice(
      step1Error,
      'File is too large. Please upload a file of 10 MB or smaller.'
    );

    selectedFile = null;

    dropzoneText.textContent =
      'Drag & drop a file, or click to browse';

    toStep2Btn.disabled = true;

    return;
  }


  // ==========================================================
  // FILE ACCEPTED
  // ==========================================================

  selectedFile = file;

  dropzoneText.textContent = file.name;

  toStep2Btn.disabled = false;

}


toStep2Btn.addEventListener('click', () => {

  if (!selectedFile) return;

  goToStep(2);

  runAnalysis(selectedFile);

});


// ============================================================
// STEP 2 — PROCESSING
// ============================================================

const processStage =
  document.getElementById('processStage');

const processBar =
  document.getElementById('processBar');

const step2Error =
  document.getElementById('step2Error');

const backToStep1Btn =
  document.getElementById('backToStep1Btn');


const STAGE_SETS = {

  pdf: [

    {
      label: 'Uploading file…',
      target: 25
    },

    {
      label: 'Reading PDF text layer…',
      target: 60
    },

    {
      label: 'Scoring the post…',
      target: 90
    }

  ],

  image: [

    {
      label: 'Uploading image…',
      target: 15
    },

    {
      label: 'Running OCR — this can take a moment…',
      target: 65
    },

    {
      label: 'Scoring the post…',
      target: 90
    }

  ]

};


function startProgress(fileType) {

  const stages =
    fileType === 'application/pdf'
      ? STAGE_SETS.pdf
      : STAGE_SETS.image;


  let progress = 2;

  let stageIndex = 0;


  processStage.textContent =
    stages[0].label;

  processBar.style.width = '2%';


  processInterval = setInterval(() => {

    const target =
      stages[stageIndex]?.target ?? 90;


    if (progress < target) {

      progress += Math.max(
        1,
        (target - progress) * 0.08
      );

      processBar.style.width =
        `${Math.min(progress, 90)}%`;

    }

    else if (
      stageIndex < stages.length - 1
    ) {

      stageIndex += 1;

      processStage.textContent =
        stages[stageIndex].label;

    }

  }, 150);

}


function stopProgress() {

  clearInterval(processInterval);

  processBar.style.width = '100%';

}


// ============================================================
// RUN ANALYSIS
// ============================================================

async function runAnalysis(file) {

  hide(step2Error);

  backToStep1Btn.classList.add('hidden');

  processBar.style.width = '2%';

  startProgress(file.type);


  try {

    const formData = new FormData();

    formData.append(
      'file',
      file
    );

    formData.append(
      'platform',
      selectedPlatform
    );


    const res = await fetch(
      `${API_URL}/api/extract`,
      {
        method: 'POST',
        body: formData
      }
    );


    const data = await res.json();


    if (!res.ok) {

      throw new Error(
        data.error ||
        'Something went wrong.'
      );

    }


    stopProgress();

    renderResults(data);

    goToStep(3);

  }

  catch (err) {

    stopProgress();


    const message =
      err.message === 'Failed to fetch'

        ? `Could not reach the backend at ${API_URL}. Is the Flask server running (py run.py)?`

        : err.message;


    showNotice(
      step2Error,
      message
    );


    backToStep1Btn.classList.remove(
      'hidden'
    );

  }

}


// ============================================================
// BACK BUTTON
// ============================================================

backToStep1Btn.addEventListener(
  'click',
  () => {

    resetWizard();

    goToStep(1);

  }
);


// ============================================================
// STEP 3 — RESULTS
// ============================================================

function renderResults(data) {

  const analysis =
    data.analysis;


  renderScore(
    analysis.readiness
  );


  renderMetrics(
    analysis.metrics,
    analysis.readability,
    analysis.tone
  );


  document.getElementById(
    'rewrittenCaption'
  ).textContent =
    analysis.rewritten_caption;


  renderHashtags(
    analysis.hashtag_ideas
  );


  renderNotes(
    analysis.notes
  );


  document.getElementById(
    'extractedText'
  ).textContent =
    data.extracted_text;


  document.getElementById(
    'extractMethod'
  ).textContent =
    data.method;


  document.getElementById(
    'resultPlatform'
  ).textContent =
    analysis.platform ||
    selectedPlatform;

}


// ============================================================
// SCORE
// ============================================================

function renderScore(readiness) {

  document.getElementById(
    'scoreValue'
  ).textContent =
    readiness.score;


  document.getElementById(
    'scoreBand'
  ).textContent =
    `${readiness.band} readiness`;


  const fill =
    document.getElementById(
      'meterFill'
    );


  fill.style.width =
    `${readiness.score}%`;


  fill.style.background =
    readiness.score >= 75
      ? 'var(--good)'
      : readiness.score >= 50
        ? 'var(--warn)'
        : 'var(--bad)';


  const list =
    document.getElementById(
      'breakdownList'
    );


  list.innerHTML = '';


  readiness.breakdown.forEach((b) => {

    const li =
      document.createElement('li');


    li.innerHTML =
      `<span>${b.factor}</span><span>${b.points}/${b.max}</span>`;


    list.appendChild(li);

  });

}


// ============================================================
// METRICS
// ============================================================

function metricCard(label, value, tone) {

  const div =
    document.createElement('div');


  div.className =
    'metric-card';


  div.innerHTML = `
    <p class="metric-label">
      ${label}
    </p>

    <p class="metric-value ${tone ? `tone-${tone}` : ''}">
      ${value}
    </p>
  `;


  return div;

}


function renderMetrics(
  metrics,
  readability,
  tone
) {

  const grid =
    document.getElementById(
      'metricsGrid'
    );


  grid.innerHTML = '';


  const toneTone =
    tone.label === 'Positive'
      ? 'good'
      : tone.label === 'Negative'
        ? 'bad'
        : null;


  const readabilityTone =
    readability.score == null
      ? null
      : readability.score >= 60
        ? 'good'
        : readability.score >= 40
          ? 'warning'
          : 'bad';


  grid.appendChild(
    metricCard(
      'Words',
      metrics.word_count
    )
  );


  grid.appendChild(
    metricCard(
      'Hashtags',
      metrics.hashtag_count
    )
  );


  grid.appendChild(
    metricCard(
      'Mentions',
      metrics.mention_count
    )
  );


  grid.appendChild(
    metricCard(
      'Emojis',
      metrics.emoji_count
    )
  );


  grid.appendChild(
    metricCard(
      'Readability',
      readability.score != null
        ? `${readability.score} · ${readability.label}`
        : 'N/A',
      readabilityTone
    )
  );


  grid.appendChild(
    metricCard(
      'Tone',
      `${tone.label} (${tone.polarity})`,
      toneTone
    )
  );


  grid.appendChild(
    metricCard(
      'Call-to-action',
      metrics.has_cta
        ? 'Yes'
        : 'No',
      metrics.has_cta
        ? 'good'
        : 'warning'
    )
  );


  grid.appendChild(
    metricCard(
      'Question hook',
      metrics.question_marks > 0
        ? 'Yes'
        : 'No',
      metrics.question_marks > 0
        ? 'good'
        : 'warning'
    )
  );

}


// ============================================================
// HASHTAGS
// ============================================================

function renderHashtags(hashtags) {

  const row =
    document.getElementById(
      'hashtagChips'
    );


  row.innerHTML = '';


  hashtags.forEach((tag) => {

    const chip =
      document.createElement('span');


    chip.className =
      'chip';


    chip.innerHTML =
      `${tag} <button data-copy="${tag}">⧉</button>`;


    row.appendChild(chip);

  });


  document.getElementById(
    'copyAllHashtags'
  ).onclick = () =>
    copyText(
      hashtags.join(' ')
    );

}


// ============================================================
// NOTES
// ============================================================

function renderNotes(notes) {

  const list =
    document.getElementById(
      'notesList'
    );


  list.innerHTML = '';


  notes.forEach((n) => {

    const li =
      document.createElement('li');


    li.className =
      `note-${n.severity}`;


    li.innerHTML =
      `<strong>${n.type}:</strong> ${n.message}`;


    list.appendChild(li);

  });

}


// ============================================================
// RESET
// ============================================================

document.getElementById(
  'startOverBtn'
).addEventListener(
  'click',
  () => {

    resetWizard();

    goToStep(1);

  }
);


function resetWizard() {

  selectedFile = null;

  fileInput.value = '';

  dropzoneText.textContent =
    'Drag & drop a file, or click to browse';


  toStep2Btn.disabled = true;


  hide(step1Error);

  hide(step2Error);


  selectedPlatform =
    'Instagram';


  platformSelect.value =
    'Instagram';

}


// ============================================================
// COPY TO CLIPBOARD
// ============================================================

function copyText(text) {

  navigator.clipboard
    .writeText(text)
    .catch(() => {

      // Clipboard API unavailable.

    });

}


document.addEventListener(
  'click',
  (e) => {

    const targetBtn =
      e.target.closest(
        '[data-copy-target]'
      );


    if (targetBtn) {

      const el =
        document.getElementById(
          targetBtn.dataset.copyTarget
        );


      copyText(
        el.textContent
      );


      flashCopied(
        targetBtn
      );


      return;

    }


    const chipBtn =
      e.target.closest(
        '[data-copy]'
      );


    if (chipBtn) {

      copyText(
        chipBtn.dataset.copy
      );

    }

  }
);


function flashCopied(btn) {

  const original =
    btn.textContent;


  btn.textContent =
    '✓ Copied';


  btn.classList.add(
    'copied'
  );


  setTimeout(() => {

    btn.textContent =
      original;

    btn.classList.remove(
      'copied'
    );

  }, 1200);

}


// ============================================================
// HISTORY
// ============================================================

const historyOverlay =
  document.getElementById(
    'historyOverlay'
  );


document.getElementById(
  'openHistoryBtn'
).addEventListener(
  'click',
  () => {

    historyOverlay.classList.remove(
      'hidden'
    );

    loadHistory();

  }
);


document.getElementById(
  'closeHistoryBtn'
).addEventListener(
  'click',
  closeHistory
);


document.getElementById(
  'historyScrim'
).addEventListener(
  'click',
  closeHistory
);


function closeHistory() {

  historyOverlay.classList.add(
    'hidden'
  );

}


async function loadHistory() {

  const container =
    document.getElementById(
      'historyList'
    );


  const clearBtn =
    document.getElementById(
      'clearHistoryBtn'
    );


  container.innerHTML =
    '<p class="empty-state">Loading…</p>';


  try {

    const res =
      await fetch(
        `${API_URL}/api/history`
      );


    const data =
      await res.json();


    const items =
      data.items || [];


    if (items.length === 0) {

      container.innerHTML =
        '<p class="empty-state">No analyses yet. Run one and it will show up here.</p>';


      clearBtn.classList.add(
        'hidden'
      );


      return;

    }


    clearBtn.classList.remove(
      'hidden'
    );


    clearBtn.onclick =
      async () => {

        await fetch(
          `${API_URL}/api/history`,
          {
            method: 'DELETE'
          }
        );

        loadHistory();

      };


    container.innerHTML = '';


    items.forEach((item) => {

      const div =
        document.createElement(
          'div'
        );


      div.className =
        'history-item';


      const tone =
        item.readiness_score >= 75
          ? 'good'
          : item.readiness_score >= 50
            ? 'warning'
            : 'bad';


      const swatch =
        tone === 'good'
          ? 'background: var(--good-soft); color: var(--good)'
          : tone === 'warning'
            ? 'background: var(--warn-soft); color: var(--warn)'
            : 'background: var(--bad-soft); color: var(--bad)';


      div.innerHTML = `

        <div class="history-item-top">

          <span class="history-item-name">
            ${escapeHtml(item.file_name)}
          </span>

          <span
            class="history-score"
            style="${swatch}">
            ${item.readiness_score}/100
          </span>

        </div>

        <p class="history-meta">
          ${new Date(item.timestamp).toLocaleString()}
          · ${escapeHtml(item.method)}
          · ${escapeHtml(item.tone)}
        </p>

        <p class="history-preview">
          ${escapeHtml(item.text_preview)}
        </p>

      `;


      container.appendChild(
        div
      );

    });

  }

  catch {

    container.innerHTML =
      `<p class="empty-state">
        Could not reach the backend at ${API_URL}.
        Is the Flask server running?
      </p>`;

  }

}


// ============================================================
// ESCAPE HTML
// ============================================================

function escapeHtml(str) {

  const div =
    document.createElement(
      'div'
    );


  div.textContent =
    str;


  return div.innerHTML;

}


// ============================================================
// HELPERS
// ============================================================

function showNotice(
  el,
  message
) {

  el.textContent =
    message;

  el.classList.remove(
    'hidden'
  );

}


function hide(el) {

  el.classList.add(
    'hidden'
  );

  el.textContent =
    '';

}