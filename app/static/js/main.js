/**
 * TaggedByBelle - Main JavaScript
 * Handles interactions, animations, and dynamic UI elements
 */




document.addEventListener('DOMContentLoaded', () => {
  initDropdowns();
  initModals();
  initToasts();
  initCountdowns();
  initAnimations();
  initFormValidation();
});




function initDropdowns() {
  const dropdowns = document.querySelectorAll('[data-dropdown]');

  dropdowns.forEach(dropdown => {
    const trigger = dropdown.querySelector('[data-dropdown-trigger]');
    const menu = dropdown.querySelector('[data-dropdown-menu]');

    if (!trigger || !menu) return;

    trigger.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = dropdown.classList.contains('open');


      document.querySelectorAll('[data-dropdown].open').forEach(d => {
        if (d !== dropdown) d.classList.remove('open');
      });


      dropdown.classList.toggle('open', !isOpen);
    });
  });


  document.addEventListener('click', (e) => {
    if (!e.target.closest('[data-dropdown]')) {
      document.querySelectorAll('[data-dropdown].open').forEach(d => {
        d.classList.remove('open');
      });
    }
  });
}




function initModals() {

  document.querySelectorAll('[data-modal-open]').forEach(trigger => {
    trigger.addEventListener('click', (e) => {
      e.preventDefault();
      const modalId = trigger.getAttribute('data-modal-open');
      openModal(modalId);
    });
  });


  document.querySelectorAll('[data-modal-close]').forEach(trigger => {
    trigger.addEventListener('click', (e) => {
      e.preventDefault();
      const modal = trigger.closest('[data-modal]');
      if (modal) closeModal(modal.id);
    });
  });


  document.querySelectorAll('[data-modal]').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closeModal(modal.id);
      }
    });
  });


  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      const openModal = document.querySelector('[data-modal].is-open');
      if (openModal) closeModal(openModal.id);
    }
  });
}

function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (!modal) return;

  modal.classList.add('is-open');
  document.body.style.overflow = 'hidden';


  const firstInput = modal.querySelector('input, textarea, select');
  if (firstInput) setTimeout(() => firstInput.focus(), 100);
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (!modal) return;

  modal.classList.remove('is-open');
  document.body.style.overflow = '';


  const form = modal.querySelector('form');
  if (form) form.reset();
}




let toastContainer = null;

function initToasts() {

  if (!document.getElementById('toast-container')) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toast-container';
    toastContainer.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 9999;
      display: flex;
      flex-direction: column;
      gap: 12px;
      pointer-events: none;
    `;
    document.body.appendChild(toastContainer);
  } else {
    toastContainer = document.getElementById('toast-container');
  }
}

function showToast(message, type = 'info', duration = 3000) {
  if (!toastContainer) initToasts();

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.style.cssText = `
    background: var(--surface);
    border: 1px solid var(--border-default);
    border-radius: var(--radius-lg);
    padding: 16px 20px;
    min-width: 300px;
    max-width: 400px;
    box-shadow: var(--shadow-xl);
    pointer-events: auto;
    animation: slideIn 0.3s ease-out;
    display: flex;
    align-items: center;
    gap: 12px;
  `;

  const icon = getToastIcon(type);
  const text = document.createElement('span');
  text.textContent = message;
  text.style.cssText = 'flex: 1; color: var(--text-primary); font-size: 14px;';

  toast.appendChild(icon);
  toast.appendChild(text);

  toastContainer.appendChild(toast);


  setTimeout(() => {
    toast.style.animation = 'slideOut 0.3s ease-out';
    setTimeout(() => toast.remove(), 300);
  }, duration);


  toast.addEventListener('click', () => {
    toast.style.animation = 'slideOut 0.3s ease-out';
    setTimeout(() => toast.remove(), 300);
  });
}

function getToastIcon(type) {
  const icon = document.createElement('span');
  icon.style.cssText = 'font-size: 20px; flex-shrink: 0;';

  switch(type) {
    case 'success':
      icon.textContent = '✓';
      icon.style.color = 'var(--success)';
      break;
    case 'error':
      icon.textContent = '✕';
      icon.style.color = 'var(--error)';
      break;
    case 'warning':
      icon.textContent = '⚠';
      icon.style.color = 'var(--warning)';
      break;
    default:
      icon.textContent = 'ℹ';
      icon.style.color = 'var(--info)';
  }

  return icon;
}


if (!document.getElementById('toast-animations')) {
  const style = document.createElement('style');
  style.id = 'toast-animations';
  style.textContent = `
    @keyframes slideIn {
      from {
        transform: translateX(100%);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }
    @keyframes slideOut {
      from {
        transform: translateX(0);
        opacity: 1;
      }
      to {
        transform: translateX(100%);
        opacity: 0;
      }
    }
  `;
  document.head.appendChild(style);
}




function initCountdowns() {
  updateCountdowns();
  setInterval(updateCountdowns, 1000);
}

function updateCountdowns() {
  const countdowns = document.querySelectorAll('[data-countdown]');

  countdowns.forEach(element => {
    const dueDate = new Date(element.getAttribute('data-countdown'));
    const now = new Date();
    const diff = dueDate - now;

    if (diff < 0) {
      element.textContent = 'Overdue';
      element.style.color = 'var(--error)';
      return;
    }

    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((diff % (1000 * 60)) / 1000);

    if (days > 0) {
      element.textContent = `${days}d ${hours}h ${minutes}m`;
    } else if (hours > 0) {
      element.textContent = `${hours}h ${minutes}m ${seconds}s`;
    } else {
      element.textContent = `${minutes}m ${seconds}s`;
      if (minutes < 10) {
        element.style.color = 'var(--error)';
      }
    }
  });
}




function initAnimations() {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('fade-in');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.1 }
  );

  document.querySelectorAll('[data-animate]').forEach(el => {
    observer.observe(el);
  });
}




function initFormValidation() {
  const forms = document.querySelectorAll('[data-validate]');

  forms.forEach(form => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();


      form.querySelectorAll('.form-error').forEach(error => error.remove());
      form.querySelectorAll('.is-invalid').forEach(input => input.classList.remove('is-invalid'));


      const isValid = validateForm(form);

      if (isValid) {

        const submitBtn = form.querySelector('[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner"></span> Loading...';


        try {
          form.submit();
        } catch (error) {
          submitBtn.disabled = false;
          submitBtn.textContent = originalText;
          showToast('An error occurred. Please try again.', 'error');
        }
      }
    });
  });
}

function validateForm(form) {
  let isValid = true;
  const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');

  inputs.forEach(input => {
    if (!input.value.trim()) {
      showFieldError(input, 'This field is required');
      isValid = false;
    } else if (input.type === 'email' && !isValidEmail(input.value)) {
      showFieldError(input, 'Please enter a valid email address');
      isValid = false;
    }
  });

  return isValid;
}

function showFieldError(input, message) {
  input.classList.add('is-invalid');
  input.style.borderColor = 'var(--error)';

  const error = document.createElement('div');
  error.className = 'form-error';
  error.textContent = message;
  input.parentElement.appendChild(error);
}

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}




function initTabs() {
  document.querySelectorAll('[data-tab]').forEach(tab => {
    tab.addEventListener('click', () => {
      const targetId = tab.getAttribute('data-tab');
      const tabGroup = tab.closest('[data-tabs]');


      tabGroup.querySelectorAll('[data-tab]').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');


      document.querySelectorAll('[data-tab-panel]').forEach(panel => {
        panel.classList.toggle('active', panel.id === targetId);
      });
    });
  });
}






function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => {
    showToast('Copied to clipboard!', 'success', 2000);
  }).catch(() => {
    showToast('Failed to copy', 'error');
  });
}


function formatCurrency(amount) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'EUR'
  }).format(amount);
}


function formatDate(date) {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  }).format(new Date(date));
}


window.showToast = showToast;
window.openModal = openModal;
window.closeModal = closeModal;
window.copyToClipboard = copyToClipboard;
window.formatCurrency = formatCurrency;
window.formatDate = formatDate;

