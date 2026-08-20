# Windows Python Environment Notes for technical-trading

## Critical Finding (2026-08-19)

**System Python 3.14 FAILS** with numpy C-extension error:
```
ModuleNotFoundError: No module named 'numpy.core._multiarray_umath'
ImportError: Error importing numpy: you should not try to import numpy from its source directory
```

**Hermes venv Python 3.11 WORKS**:
- Path: `/c/Users/kho/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe`
- Packages: numpy 1.26.4, pandas 2.3.3, yfinance 1.6.0 — all compatible

## Root Cause
- Windows Store Python 3.14 (`/c/Program Files/WindowsApps/PythonSoftwareFoundation.PythonManager_.../python3`) has incompatible numpy wheel or path resolution issue
- The numpy package in Hermes venv was built for Python 3.11 ABI
- Python 3.14 cannot load numpy 1.26.4 C-extensions compiled for 3.11

## Rule for Cron Jobs & Scripts
**ALWAYS use the Hermes venv Python explicitly**:
```bash
# ✅ CORRECT
/c/Users/kho/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe script.py

# ❌ WRONG — will fail
python3 script.py
python script.py
```

## Cron Job Configuration
When creating cron jobs that run technical-trading scripts, the skill must ensure the correct Python is invoked. The `technical_signal_monitor.py` script should be called with the full venv Python path.

## Verification Command
```bash
/c/Users/kho/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe -c "import yfinance; import pandas; import numpy; print('OK:', numpy.__version__)"
```

## Package Versions (Working Set)
| Package | Version | Notes |
|---------|---------|-------|
| python | 3.11.x (venv) | Not 3.14 |
| numpy | 1.26.4 | C-extensions work |
| pandas | 2.3.3 | |
| yfinance | 1.6.0 | |
| curl_cffi | 0.16.0 | yfinance dependency |

## Future Upgrade Path
When Hermes upgrades its base Python version, rebuild venv:
```bash
cd /c/Users/kho/AppData/Local/hermes/hermes-agent
python -m venv venv --clear
./venv/Scripts/pip install yfinance pandas numpy
```