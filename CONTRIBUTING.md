# Contributing to MedClaim-GenAI

We welcome contributions across all project tiers—whether it's optimizing SQL analytics, enhancing machine learning models, updating Power BI DAX measures, or refining GenAI appeal templates.

---

## 🔄 Contribution Workflow

1. **Issues First:** For major changes or new features, please open an issue first to discuss what you would like to change.
2. **Branching Strategy:** Create a descriptive working branch:
   * Feature branch: `feature/short-description`
   * Bugfix branch: `fix/short-description`
3. **Commit Convention:** Use clear, concise commit messages (e.g., `git commit -m "feat: add provider leakage ranking measure"`).

---

## 🧪 Testing & Validation Checklist

Before submitting a pull request, please verify:
- [ ] Python scripts execute successfully without unhandled exceptions.
- [ ] SQL scripts run cleanly inside SQLite without syntax warnings.
- [ ] README and documentation are updated if new scripts or files are introduced.
- [ ] No local API keys or confidential data are exposed in the commit history.
