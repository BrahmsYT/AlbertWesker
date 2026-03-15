// Supported languages
const SUPPORTED_LANGS = ['en', 'az', 'ru'];

// Language switcher initialization
document.addEventListener('DOMContentLoaded', () => {
  const langSelect = document.getElementById('langSelect');
  if (langSelect) {
    const currentLang = getCurrentLang();
    langSelect.value = currentLang;
    
    langSelect.addEventListener('change', (e) => {
      const newLang = e.target.value;
      if (SUPPORTED_LANGS.includes(newLang)) {
        localStorage.setItem('lang', newLang);
        changeLang(newLang);
      }
    });
  }

  // Initialize sort handlers on findings (section-aware)
  initFindingsSort();
});

// Get current language safely
function getCurrentLang() {
  // Try URL param first
  const urlLang = new URLSearchParams(window.location.search).get('lang');
  if (urlLang && SUPPORTED_LANGS.includes(urlLang)) {
    return urlLang;
  }
  
  // Try localStorage
  const storedLang = localStorage.getItem('lang');
  if (storedLang && SUPPORTED_LANGS.includes(storedLang)) {
    return storedLang;
  }
  
  // Default to English
  return 'en';
}

// Safe language switching with validation
function changeLang(newLang) {
  // Validate language parameter - block any non-whitelisted values
  if (!SUPPORTED_LANGS.includes(newLang)) {
    console.warn(`Invalid language: ${newLang}. Using English.`);
    newLang = 'en';
  }
  
  // Store in localStorage
  localStorage.setItem('lang', newLang);
  
  // Build safe URL with language parameter
  try {
    const url = new URL(window.location);
    url.searchParams.set('lang', newLang);
    // Use href (string) to prevent any object injection
    window.location.href = url.toString();
  } catch (e) {
    // Fallback: simple redirect (only on same origin)
    if (window.location.protocol === location.protocol && 
        window.location.hostname === location.hostname) {
      window.location.href = window.location.href.split('?')[0] + '?lang=' + newLang;
    }
  }
}

// Section-aware findings sort (keeps AWS and General separate)
function initFindingsSort() {
  const awsSection = document.querySelector('[data-section="aws"]');
  const generalSection = document.querySelector('[data-section="general"]');
  
  if (!awsSection && !generalSection) {
    return;  // Not on result page, skip
  }
  
  // Sort AWS findings if section exists
  if (awsSection) {
    const cards = Array.from(awsSection.querySelectorAll('.finding-card'));
    const severityOrder = { 'critical': 0, 'high': 1, 'medium': 2, 'low': 3 };
    
    cards.sort((a, b) => {
      const sevA = a.querySelector('span[style*="background"]')?.textContent.toLowerCase() || 'low';
      const sevB = b.querySelector('span[style*="background"]')?.textContent.toLowerCase() || 'low';
      return (severityOrder[sevA] || 999) - (severityOrder[sevB] || 999);
    });
    
    cards.forEach(card => awsSection.appendChild(card));
  }
  
  // Sort General findings if section exists  
  if (generalSection) {
    const cards = Array.from(generalSection.querySelectorAll('.finding-card'));
    const severityOrder = { 'critical': 0, 'high': 1, 'medium': 2, 'low': 3 };
    
    cards.sort((a, b) => {
      const sevA = a.querySelector('span[style*="background"]')?.textContent.toLowerCase() || 'low';
      const sevB = b.querySelector('span[style*="background"]')?.textContent.toLowerCase() || 'low';
      return (severityOrder[sevA] || 999) - (severityOrder[sevB] || 999);
    });
    
    cards.forEach(card => generalSection.appendChild(card));
  }
}



