# Testing & Quality Setup - Quick Reference

## 🚀 One-Time Setup

```bash
# Install git hooks (pre-commit, commit-msg, pre-push)
./setup-hooks.sh

# Or manually
chmod +x setup-hooks.sh
./setup-hooks.sh
```

## 🧪 Running Tests

```bash
# Quick unit tests
uv run pytest tests/unit/ -v

# With coverage report
uv run pytest tests/unit/ --cov=src --cov-report=html

# Specific test file
uv run pytest tests/unit/models/test_vehicle.py -v

# Run only model tests
uv run pytest -m models

# Parallel execution (faster)
uv run pytest -n auto
```

## 🔍 Code Quality

```bash
# Check formatting
uv run ruff format --check .

# Auto-fix formatting
uv run ruff format .

# Run linter
uv run ruff check .

# Auto-fix lint issues
uv run ruff check --fix .

# Type checking
uv run mypy src/
```

## 🪝 Git Hooks

### Automatically Enabled After Setup

- **pre-commit**: Runs before every commit
  - Format checking
  - Linting
  - Security scans
  - Docstring validation
  
- **commit-msg**: Validates commit message format

- **pre-push**: Runs before push
  - Unit tests (all branches)
  - Integration tests + linting (main/release only)

### Skip Hooks (Use Sparingly)

```bash
git commit --no-verify
git push --no-verify
```

## 🎯 Test Coverage

Current coverage: **100%** on all models

View coverage report:

```bash
uv run pytest --cov=src --cov-report=html
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## 📁 Test Organization

```
tests/
├── unit/models/           # Model validation tests
│   ├── test_alerts.py     # 22 tests
│   ├── test_enums.py      # 18 tests
│   ├── test_messages.py   # 24 tests
│   ├── test_simulation.py # 18 tests
│   ├── test_telemetry.py  # 16 tests
│   └── test_vehicle.py    # 34 tests
└── fixtures/              # Shared test data
    └── model_fixtures.py  # All model fixtures
```

## ⚙️ CI/CD Pipeline

GitHub Actions runs on:

- Push to `main`, `release`, `feature/**`
- Pull requests to `main`, `release`

Pipeline stages:

1. **Lint** - Format + style checks
2. **Test** - Unit + integration tests
3. **Security** - Vulnerability scanning
4. **Build** - Package verification

## 🛠️ Troubleshooting

### Tests failing?

```bash
uv sync --all-extras
uv run pytest tests/unit/ -v
```

### Pre-commit issues?

```bash
pre-commit clean
pre-commit install --install-hooks
pre-commit run --all-files
```

### Hooks not running?

```bash
./setup-hooks.sh
```

## 📚 Documentation

- **Full Testing Guide**: `tests/README.md`
- **Development Guide**: `AGENTS.md`
- **Main README**: `README.md`

## ✅ Quick Health Check

```bash
# Verify everything is working
uv run pytest tests/unit/models/ -v --cov=src
uv run ruff check .
uv run mypy src/

# Should see:
# ✓ 132 tests passed
# ✓ 100% coverage on models
# ✓ No linting issues
# ✓ Type checking passed
```
