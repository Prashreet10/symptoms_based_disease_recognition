async function postPredict(payload) {
  const maxAttempts = 3;
  const retryDelay = 800; // ms
  let lastError;
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      const res = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify(payload)
      });
      if (!res.ok) {
        let data;
        try {
          data = await res.json();
        } catch (_) {
          data = {};
        }
        const errorMsg = data.error || `HTTP ${res.status}: Prediction failed`;
        throw new Error(errorMsg);
      }
      const data = await res.json();
      return data;
    } catch (error) {
      lastError = error;
      console.error(`Fetch error attempt ${attempt}:`, error);
      if (attempt < maxAttempts) {
        await new Promise(r => setTimeout(r, retryDelay));
      }
    }
  }
  throw lastError;
}

// Add smooth animations
function animateElement(element, animationClass) {
  element.classList.add(animationClass);
  setTimeout(() => element.classList.remove(animationClass), 1000);
}

document.addEventListener('click', (e) => {
  if (e.target && (e.target.id === 'add-symptom' || e.target.closest('#add-symptom'))) {
    e.preventDefault();
    addRow();
  }
  if (e.target && (e.target.classList.contains('remove') || e.target.closest('.remove'))) {
    const row = e.target.closest('.symptom-row');
    if (row) {
      // Add exit animation
      row.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
      row.style.opacity = '0';
      row.style.transform = 'translateX(-30px) scale(0.9)';
      row.style.maxHeight = row.offsetHeight + 'px';
      
      setTimeout(() => {
        row.style.maxHeight = '0';
        row.style.marginBottom = '0';
        row.style.paddingTop = '0';
        row.style.paddingBottom = '0';
      }, 100);
      
      setTimeout(() => row.remove(), 400);
    }
  }
});

function addRow() {
  const div = document.createElement('div');
  div.className = 'symptom-row d-flex gap-2 mb-3 align-items-center';
  div.style.opacity = '0';
  div.style.transform = 'translateY(-20px) scale(0.95)';
  div.innerHTML = `
    <div class="flex-grow-1">
      <label class="form-label small text-muted mb-1">
        <i class="fas fa-search me-1"></i>Symptom Name
      </label>
      <input name="symptom" list="symptoms-list" class="form-control" placeholder="e.g., fever, headache, cough" autocomplete="off" />
    </div>
    <div style="width: 120px;">
      <label class="form-label small text-muted mb-1">
        <i class="fas fa-exclamation-triangle me-1"></i>Severity (1-5)
      </label>
      <input name="severity" class="form-control" type="number" min="1" max="5" placeholder="1-5" />
    </div>
    <div style="width: 140px;">
      <label class="form-label small text-muted mb-1">
        <i class="fas fa-calendar-alt me-1"></i>Duration (days)
      </label>
      <input name="duration" class="form-control" type="number" min="1" placeholder="Days" />
    </div>
    <div class="d-flex align-items-end" style="height: 58px;">
      <button class="btn btn-outline-danger remove" type="button" title="Remove symptom">
        <i class="fas fa-times"></i>
      </button>
    </div>
  `;
  document.getElementById('symptom-list').appendChild(div);
  
  // Animate in with smooth transition
  setTimeout(() => {
    div.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
    div.style.opacity = '1';
    div.style.transform = 'translateY(0) scale(1)';
  }, 10);
  
  // Focus on the new symptom input with slight delay for better UX
  setTimeout(() => {
    const input = div.querySelector('input[name="symptom"]');
    input.focus();
    input.select();
  }, 400);
  
  // Add shake animation on add
  div.style.animation = 'shake 0.5s ease';
  setTimeout(() => {
    div.style.animation = '';
  }, 500);
}

// Add shake animation
if (!document.getElementById('shake-animation-style')) {
  const style = document.createElement('style');
  style.id = 'shake-animation-style';
  style.textContent = `
    @keyframes shake {
      0%, 100% { transform: translateX(0); }
      25% { transform: translateX(-5px); }
      75% { transform: translateX(5px); }
    }
  `;
  document.head.appendChild(style);
}

function gatherInput() {
  const rows = Array.from(document.querySelectorAll('.symptom-row'));
  const out = {};
  rows.forEach(r => {
    const s = r.querySelector('input[name=symptom]').value.trim().toLowerCase();
    if (!s) return;
    const sev = r.querySelector('input[name=severity]').value;
    const dur = r.querySelector('input[name=duration]').value;
    if (sev || dur) {
      out[s] = { presence: 1 };
      if (sev) out[s].severity = Number(sev);
      if (dur) out[s].duration = Number(dur);
    } else {
      out[s] = 1;
    }
  });
  return out;
}

function showLoading() {
  const submitBtn = document.getElementById('submit');
  const form = document.getElementById('symptom-form');
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Analyzing Symptoms...';
  submitBtn.style.opacity = '0.8';
  submitBtn.style.cursor = 'not-allowed';
  form.classList.add('loading');
  
  // Add pulsing animation
  submitBtn.style.animation = 'pulse 2s ease-in-out infinite';
}

function hideLoading() {
  const submitBtn = document.getElementById('submit');
  const form = document.getElementById('symptom-form');
  submitBtn.disabled = false;
  submitBtn.innerHTML = '<i class="fas fa-brain me-2"></i>Analyze & Predict';
  submitBtn.style.opacity = '1';
  submitBtn.style.cursor = 'pointer';
  submitBtn.style.animation = '';
  form.classList.remove('loading');
}

// Add pulse animation style
if (!document.getElementById('pulse-animation-style')) {
  const style = document.createElement('style');
  style.id = 'pulse-animation-style';
  style.textContent = `
    @keyframes pulse {
      0%, 100% {
        opacity: 0.8;
      }
      50% {
        opacity: 1;
      }
    }
  `;
  document.head.appendChild(style);
}

function displayResults(res) {
  const resultEl = document.getElementById('result');
  resultEl.classList.remove('d-none');
  resultEl.style.opacity = '0';
  resultEl.style.transform = 'translateY(30px)';
  
  // Animate result section in
  setTimeout(() => {
    resultEl.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
    resultEl.style.opacity = '1';
    resultEl.style.transform = 'translateY(0)';
  }, 10);
  
  // Update prediction
  const predictionEl = document.getElementById('prediction');
  const confidence = Math.round((res.confidence || 0) * 100);
  let confidenceColor, confidenceBadge;
  
  if (confidence >= 70) {
    confidenceColor = 'var(--accent)';
    confidenceBadge = '<span style="background: rgba(240, 47, 52, 0.15); color: var(--accent); padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.875rem; font-weight: 600; margin-left: 1rem;">High Confidence</span>';
  } else if (confidence >= 50) {
    confidenceColor = '#f59e0b';
    confidenceBadge = '<span style="background: rgba(245, 158, 11, 0.15); color: #f59e0b; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.875rem; font-weight: 600; margin-left: 1rem;">Moderate Confidence</span>';
  } else {
    confidenceColor = 'var(--muted)';
    confidenceBadge = '<span style="background: rgba(107, 114, 128, 0.15); color: var(--muted); padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.875rem; font-weight: 600; margin-left: 1rem;">Low Confidence</span>';
  }
  
  predictionEl.innerHTML = `
    <div style="display: flex; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
      <strong style="font-size: 1.875rem; color: var(--accent);">${res.prediction}</strong>
      <span style="color: ${confidenceColor}; font-size: 1.125rem; font-weight: 600;">
        ${confidence}%
      </span>
      ${confidenceBadge}
    </div>
  `;
  
  // Update top features
  const tf = document.getElementById('top-features');
  tf.innerHTML = '';
  const features = res.top_features_by_shap || res.top_features_by_model || [];
  if (features.length === 0) {
    tf.innerHTML = '<li style="color: var(--muted); padding: 1rem; text-align: center; background: #f8f5f0; border-radius: 12px;">No feature data available</li>';
  } else {
    features.forEach((s, index) => {
      const li = document.createElement('li');
      li.textContent = s;
      li.style.opacity = '0';
      li.style.transform = 'translateX(-20px)';
      li.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
      tf.appendChild(li);
      setTimeout(() => {
        li.style.opacity = '1';
        li.style.transform = 'translateX(0)';
      }, 150 + (index * 80));
    });
  }
  
  // Update tests
  const tt = document.getElementById('tests');
  tt.innerHTML = '';
  const tests = res.recommended_tests || [];
  if (tests.length === 0) {
    tt.innerHTML = '<li style="color: var(--muted); padding: 1rem; text-align: center; background: #f8f5f0; border-radius: 12px;">No specific tests recommended at this time</li>';
  } else {
    tests.forEach((t, index) => {
      const li = document.createElement('li');
      li.innerHTML = `<i class="fas fa-vial" style="color: var(--accent); margin-right: 0.5rem;"></i>${t}`;
      li.style.opacity = '0';
      li.style.transform = 'translateX(-20px)';
      li.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
      tt.appendChild(li);
      setTimeout(() => {
        li.style.opacity = '1';
        li.style.transform = 'translateX(0)';
      }, 150 + (index * 80));
    });
  }
  
  // Scroll to results with smooth animation
  setTimeout(() => {
    resultEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, 200);

  const dl = document.getElementById('download-report-pdf');
  if (dl && res.download_url) {
    dl.href = res.download_url;
    dl.classList.remove('d-none');
  } else if (dl) {
    dl.classList.add('d-none');
  }
}

document.addEventListener('submit', async (ev) => {
  if (ev.target && ev.target.id === 'symptom-form') {
    ev.preventDefault();
    const symptoms = gatherInput();
    
    if (Object.keys(symptoms).length === 0) {
      // Better error notification
      showNotification('Please enter at least one symptom', 'error');
      // Shake the form
      const form = document.getElementById('symptom-form');
      form.style.animation = 'shake 0.5s ease';
      setTimeout(() => {
        form.style.animation = '';
      }, 500);
      return;
    }
    
    try {
      showLoading();
      // Get patient name
      const patientNameInput = document.getElementById('patient-name');
      const patient_name = patientNameInput ? patientNameInput.value.trim() : '';
      const res = await postPredict({ symptoms, patient_name });
      hideLoading();
      displayResults(res);
      showNotification('Prediction completed successfully!', 'success');
    } catch (error) {
      hideLoading();
      const errorMessage = error.message || 'An error occurred while predicting. Please try again.';
      showNotification(errorMessage, 'error');
      console.error('Prediction error:', error);
    }
  }
});

// Notification system
function showNotification(message, type = 'info') {
  // Remove existing notifications
  const existing = document.querySelector('.notification');
  if (existing) {
    existing.remove();
  }
  
  const notification = document.createElement('div');
  notification.className = `notification notification-${type}`;
  notification.innerHTML = `
    <div style="display: flex; align-items: center; gap: 0.75rem;">
      <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
      <span>${message}</span>
    </div>
  `;
  
  // Add styles
  notification.style.cssText = `
    position: fixed;
    top: 100px;
    right: 20px;
    background: ${type === 'success' ? '#10b981' : type === 'error' ? '#dc2626' : '#3b82f6'};
    color: white;
    padding: 1rem 1.5rem;
    border-radius: 12px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
    z-index: 10000;
    animation: slideInRight 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    max-width: 400px;
    font-weight: 500;
  `;
  
  document.body.appendChild(notification);
  
  // Auto remove after 4 seconds
  setTimeout(() => {
    notification.style.animation = 'slideOutRight 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
    setTimeout(() => notification.remove(), 400);
  }, 4000);
}

// Add notification animations
if (!document.getElementById('notification-animations')) {
  const style = document.createElement('style');
  style.id = 'notification-animations';
  style.textContent = `
    @keyframes slideInRight {
      from {
        transform: translateX(400px);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }
    @keyframes slideOutRight {
      from {
        transform: translateX(0);
        opacity: 1;
      }
      to {
        transform: translateX(400px);
        opacity: 0;
      }
    }
  `;
  document.head.appendChild(style);
}

// Smooth scroll for in-page anchors (e.g. #section). Exclude href="#" placeholders
// so they are not prevented from navigating when JS sets a real URL (e.g. PDF download).
document.querySelectorAll('a[href^="#"]:not([href="#"])').forEach((anchor) => {
  anchor.addEventListener('click', function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      target.scrollIntoView({ behavior: 'smooth' });
    }
  });
});
