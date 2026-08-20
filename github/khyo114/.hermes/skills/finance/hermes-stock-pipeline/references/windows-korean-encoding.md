# Windows/WSL Korean Encoding Setup

## Problem

Hermes on Windows/WSL shows garbled Korean text or fails to display Korean properly.

## Root Cause

- Default locale in WSL/Git Bash is often `C` or `POSIX`
- Windows Terminal default encoding may not be UTF-8
- Python `sys.stdout.encoding` may not be UTF-8

## Solution

### 1. Set Locale Environment Variables

Add to `~/.bashrc` (WSL/Git Bash):

```bash
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export PYTHONIOENCODING=utf-8
```

Then reload:
```bash
source ~/.bashrc
```

### 2. Configure in Hermes Config

Add to `~/.hermes/config.yaml`:

```yaml
terminal:
  env:
    LANG: "ko_KR.UTF-8"
    LC_ALL: "ko_KR.UTF-8"
    PYTHONIOENCODING: "utf-8"
```

Or via CLI:
```bash
hermes config set terminal.env.LANG ko_KR.UTF-8
hermes config set terminal.env.LC_ALL ko_KR.UTF-8
hermes config set terminal.env.PYTHONIOENCODING utf-8
```

### 3. Windows Terminal Settings

1. Open Windows Terminal Settings (Ctrl+,)
2. Select **Git Bash** profile
3. **Appearance** → **Text** → **Character set**: `UTF-8`
4. Save and restart terminal

### 4. Verify

```bash
# Check locale
locale

# Check Python encoding
python3 -c "import sys; print(sys.stdout.encoding)"

# Test Hermes Korean output
hermes chat -q "한글 테스트: 삼성전자 분석"
```

## Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| `locale: Cannot set LC_CTYPE` | `ko_KR.UTF-8` not available | Use `C.UTF-8` instead |
| Korean garbled in Hermes Desktop | Electron font doesn't support Korean | Change font to `JetBrains Mono`, `D2Coding`, or `NanumGothicCoding` |
| `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xbf` | CP949/EUC-KR HTML parsed as UTF-8 | Use encoding fallback in Python: try UTF-8, then CP949 |

## Python Encoding Fallback Pattern

```python
def read_html_with_fallback(filepath):
    """UTF-8 실패 시 CP949로 재시도"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(filepath, 'r', encoding='cp949') as f:
            return f.read()
```

## Windows Path Handling

```python
# Use raw strings or forward slashes
data_dir = r"C:\Users\kho\주식분석\data"  # Raw string
data_dir = "C:/Users/kho/주식분석/data"    # Forward slashes

# Avoid: backslashes without raw string (escape sequence issues)
# data_dir = "C:\Users\kho\주식분석\data"  # BAD!
```