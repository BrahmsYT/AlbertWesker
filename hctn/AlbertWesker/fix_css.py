#!/usr/bin/env python3
# Fix CSS file - remove duplicates

css_content = """:root {
  --neon-blue: #00d9ff;
  --neon-cyan: #00ffff;
  --dark-bg: #0a0f1f;
  --text-primary: #ffffff;
  --text-secondary: #a0a9ff;
  --risk-safe: #00ff00;
  --risk-warn: #ffaa00;
  --risk-danger: #ff3333;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Courier New', monospace;
  background-color: var(--dark-bg);
  color: var(--text-primary);
  line-height: 1.6;
}

a {
  color: var(--neon-blue);
  text-decoration: none;
}

.cyber-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.2rem 1.5rem;
  background: rgba(20, 24, 41, 0.7);
  border-bottom: 2px solid rgba(0, 217, 255, 0.2);
  margin-bottom: 2rem;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 700;
  font-size: 1.2rem;
}

.brand-text {
  color: var(--neon-cyan);
  text-shadow: 0 0 8px var(--neon-blue);
}

.nav-links {
  display: flex;
  gap: 1.5rem;
}

.nav-link {
  padding: 0.4rem 0.8rem;
  color: var(--text-secondary);
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: 0.2s;
}

.nav-link:hover,
.nav-link.active {
  color: var(--neon-cyan);
  border-bottom-color: var(--neon-cyan);
}

.container, .hero-container, .result-container, .lists-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1.5rem;
}

.hero-title {
  font-size: 3rem;
  font-weight: 800;
  color: var(--neon-cyan);
  text-shadow: 0 0 20px var(--neon-blue);
  letter-spacing: 2px;
  margin-bottom: 1.5rem;
}

.scan-card {
  padding: 2rem;
  text-align: center;
  margin-bottom: 2rem;
  background: rgba(20, 24, 41, 0.4);
  border: 1px solid rgba(0, 217, 255, 0.2);
  border-radius: 12px;
}

.scan-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.input-wrapper {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.cyber-input {
  flex: 1;
  padding: 1rem;
  background: rgba(10, 15, 31, 0.5);
  border: 2px solid var(--neon-blue);
  border-radius: 6px;
  color: var(--text-primary);
  font-family: monospace;
  outline: none;
}

.cyber-input:focus {
  border-color: var(--neon-cyan);
  box-shadow: 0 0 15px var(--neon-blue);
}

.cyber-btn {
  padding: 1rem 1.8rem;
  background: linear-gradient(135deg, var(--neon-blue), var(--neon-cyan));
  border: none;
  border-radius: 6px;
  color: var(--dark-bg);
  font-weight: 700;
  cursor: pointer;
  transition: 0.2s;
}

.cyber-btn:hover {
  box-shadow: 0 0 20px var(--neon-cyan);
  transform: translateY(-2px);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-top: 2rem;
}

.info-card {
  padding: 1.5rem;
  background: rgba(20, 24, 41, 0.3);
  border: 1px solid rgba(0, 217, 255, 0.2);
  border-radius: 8px;
  text-align: center;
}

.info-card h3 {
  color: var(--neon-cyan);
  margin-bottom: 0.5rem;
}

.alert {
  padding: 1rem 1.5rem;
  border-radius: 6px;
  margin-bottom: 1.5rem;
  display: flex;
  gap: 0.8rem;
}

.alert-error {
  background: rgba(255, 51, 51, 0.1);
  border: 2px solid rgba(255, 51, 51, 0.3);
  color: var(--risk-danger);
}

.alert-success {
  background: rgba(0, 255, 0, 0.1);
  border: 2px solid rgba(0, 255, 0, 0.3);
  color: var(--risk-safe);
}

.result-header h1 {
  font-size: 2rem;
  color: var(--neon-cyan);
  margin-bottom: 0.5rem;
}

.target-info {
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin-bottom: 1.5rem;
}

.trusted-badge {
  display: inline-block;
  padding: 0.3rem 0.7rem;
  background: rgba(0, 255, 0, 0.2);
  border: 1px solid var(--risk-safe);
  color: var(--risk-safe);
  border-radius: 4px;
  font-size: 0.8rem;
  margin-left: 0.5rem;
}

.risk-score-section {
  display: flex;
  justify-content: space-between;
  gap: 2rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}

.risk-card {
  padding: 2rem;
  border-radius: 12px;
  flex: 1;
  min-width: 280px;
  border: 2px solid;
  background: rgba(20, 24, 41, 0.4);
  text-align: center;
}

.risk-safe {
  border-color: var(--risk-safe);
  box-shadow: 0 0 20px rgba(0, 255, 0, 0.3);
}

.risk-medium {
  border-color: var(--risk-warn);
  box-shadow: 0 0 20px rgba(255, 170, 0, 0.3);
}

.risk-high {
  border-color: var(--risk-danger);
  box-shadow: 0 0 20px rgba(255, 51, 51, 0.3);
}

.score-number {
  font-size: 3.5rem;
  font-weight: 800;
}

.risk-safe .score-number {
  color: var(--risk-safe);
  text-shadow: 0 0 10px var(--risk-safe);
}

.risk-medium .score-number {
  color: var(--risk-warn);
}

.risk-high .score-number {
  color: var(--risk-danger);
}

.meta-panel {
  padding: 1.5rem;
  margin-bottom: 2rem;
  background: rgba(20, 24, 41, 0.4);
  border: 1px solid rgba(0, 217, 255, 0.2);
  border-radius: 8px;
}

.meta-panel h2 {
  font-size: 1.1rem;
  color: var(--neon-cyan);
  margin-bottom: 1rem;
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
}

.meta-item {
  padding: 0.8rem;
  background: rgba(10, 15, 31, 0.3);
  border-left: 3px solid var(--neon-blue);
}

.meta-label {
  color: var(--text-secondary);
  font-size: 0.85rem;
  margin-bottom: 0.3rem;
}

.meta-val {
  color: var(--neon-cyan);
  font-family: monospace;
}

.port-panel {
  padding: 1.5rem;
  margin-bottom: 2rem;
  background: rgba(20, 24, 41, 0.4);
  border: 1px solid rgba(0, 217, 255, 0.2);
  border-radius: 8px;
}

.port-panel h2 {
  font-size: 1.1rem;
  color: var(--neon-cyan);
  margin-bottom: 1rem;
}

.port-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.port-table th {
  padding: 0.8rem;
  background: rgba(0, 217, 255, 0.1);
  color: var(--neon-cyan);
  border-bottom: 2px solid var(--neon-blue);
}

.port-table td {
  padding: 0.7rem 0.8rem;
  border-bottom: 1px solid rgba(0, 217, 255, 0.2);
}

.port-num {
  color: var(--neon-blue);
  font-weight: 700;
}

.sev-pill {
  display: inline-block;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  border: 1px solid;
  font-size: 0.85rem;
  margin-right: 0.5rem;
}

.pill-critical {
  background: rgba(255, 51, 51, 0.1);
  border-color: var(--risk-danger);
  color: var(--risk-danger);
}

.pill-high {
  background: rgba(255, 170, 0, 0.1);
  border-color: var(--risk-warn);
  color: var(--risk-warn);
}

.pill-low {
  background: rgba(0, 255, 0, 0.1);
  border-color: var(--risk-safe);
  color: var(--risk-safe);
}

.findings {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 2rem;
}

.finding-card {
  padding: 1.5rem;
  background: rgba(20, 24, 41, 0.4);
  border: 2px solid;
  border-radius: 8px;
}

.finding-safe {
  border-color: var(--risk-safe);
}

.finding-warn {
  border-color: var(--risk-warn);
}

.finding-danger {
  border-color: var(--risk-danger);
}

.finding-card h3 {
  color: var(--neon-cyan);
  margin-bottom: 0.5rem;
}

.finding-evidence {
  margin: 0.8rem 0;
  padding: 0.8rem;
  background: rgba(10, 15, 31, 0.3);
  border-left: 2px solid var(--neon-blue);
}

.no-findings {
  padding: 2rem;
  text-align: center;
  background: rgba(0, 255, 0, 0.1);
  border: 2px solid var(--risk-safe);
  color: var(--risk-safe);
}

.tabs {
  display: flex;
  border-bottom: 2px solid rgba(0, 217, 255, 0.2);
  margin-bottom: 1.5rem;
}

.tab {
  padding: 0.8rem 1.5rem;
  background: transparent;
  color: var(--text-secondary);
  border: none;
  cursor: pointer;
  border-bottom: 2px solid transparent;
}

.tab.active {
  color: var(--neon-cyan);
  border-bottom-color: var(--neon-cyan);
}

.tab-panel {
  display: none;
}

.tab-panel.active {
  display: block;
}

.list-section {
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  background: rgba(20, 24, 41, 0.4);
  border: 1px solid rgba(0, 217, 255, 0.2);
  border-radius: 8px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.section-header h2 {
  color: var(--neon-cyan);
  margin: 0;
}

.list-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}

.list-table th {
  padding: 0.8rem;
  background: rgba(0, 217, 255, 0.1);
  color: var(--neon-cyan);
  border-bottom: 2px solid var(--neon-blue);
}

.list-table td {
  padding: 0.7rem 0.8rem;
  border-bottom: 1px solid rgba(0, 217, 255, 0.2);
}

.td-domain {
  font-family: monospace;
  color: var(--neon-blue);
}

.td-risk-safe {
  color: var(--risk-safe);
}

.td-risk-warn {
  color: var(--risk-warn);
}

.td-risk-danger {
  color: var(--risk-danger);
}

.btn-small {
  padding: 0.4rem 0.7rem;
  border: 1px solid var(--neon-blue);
  cursor: pointer;
  background: rgba(0, 217, 255, 0.1);
  color: var(--neon-blue);
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.8rem;
}

.btn-small:hover {
  background: rgba(0, 217, 255, 0.2);
}

.btn-remove {
  border-color: var(--risk-danger);
  color: var(--risk-danger);
  background: rgba(255, 51, 51, 0.1);
}

.stats-bar {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  padding: 1rem;
  background: rgba(20, 24, 41, 0.4);
  border: 1px solid rgba(0, 217, 255, 0.2);
  border-radius: 8px;
  text-align: center;
}

.stat-num {
  font-size: 2rem;
  color: var(--neon-cyan);
  font-weight: 700;
}

.stat-label {
  color: var(--text-secondary);
  font-size: 0.85rem;
  margin-top: 0.3rem;
}

.whitelist-form {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.form-input {
  flex: 1;
  padding: 0.7rem;
  background: rgba(10, 15, 31, 0.5);
  border: 1px solid var(--neon-blue);
  border-radius: 4px;
  color: var(--text-primary);
  font-family: monospace;
  outline: none;
}

.form-input:focus {
  border-color: var(--neon-cyan);
  box-shadow: 0 0 10px var(--neon-blue);
}

.toolbar {
  display: flex;
  gap: 0.8rem;
  margin-bottom: 1.5rem;
}

.search-box {
  flex: 1;
  position: relative;
}

.search-box input {
  width: 100%;
  padding: 0.7rem 0.8rem;
  background: rgba(10, 15, 31, 0.5);
  border: 1px solid var(--neon-blue);
  border-radius: 6px;
  color: var(--text-primary);
  font-family: monospace;
  outline: none;
}

.search-box input:focus {
  border-color: var(--neon-cyan);
  box-shadow: 0 0 10px var(--neon-blue);
}

.cyber-footer {
  text-align: center;
  padding: 2rem 1.5rem;
  color: var(--text-secondary);
  border-top: 1px solid rgba(0, 217, 255, 0.2);
  margin-top: 3rem;
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 2rem;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .stats-bar {
    grid-template-columns: repeat(2, 1fr);
  }
}
"""

with open('static/style.css', 'w') as f:
    f.write(css_content)

print("CSS file fixed!")
