# Python Linting Setup

This document describes the comprehensive linting solution implemented for the Pokemon Blue AI Agent project to prevent syntax and style issues.

## Overview

The project uses a comprehensive set of Python linting tools to ensure code quality:

- **Black** - Code formatting
- **isort** - Import sorting
- **Flake8** - Style and error checking
- **MyPy** - Type checking
- **Pre-commit** - Automated linting on git commits

## Configuration Files

### `.flake8`
Configures Flake8 with project-specific settings:
- 88 character line length (compatible with Black)
- Selected error codes (B, C, E, F, W, T4, B9)
- Excludes common directories (`.git`, `__pycache__`, etc.)

### `pyproject.toml`
Central configuration for Black, isort, and MyPy:
- Black: 88 character line length, Python 3.8+ target
- isort: Black-compatible profile
- MyPy: Strict type checking with third-party library ignores

### `.pre-commit-config.yaml`
Pre-commit hooks configuration:
- Runs all linting tools automatically before each commit
- Includes additional checks (trailing whitespace, YAML validation, etc.)
- Auto-fixes simple issues

### `requirements-dev.txt`
Development dependencies including all linting tools and testing utilities.

## Usage

### Quick Start

1. **Install development dependencies:**
   ```bash
   python scripts/setup_linting.py --dev
   ```

2. **Set up pre-commit hooks:**
   ```bash
   python scripts/setup_linting.py --pre-commit
   ```

3. **Run all linting checks:**
   ```bash
   python scripts/lint.py
   ```

### Individual Tools

Run specific tools using the lint script:

```bash
# Format code with Black
python scripts/lint.py --tool black --fix

# Sort imports with isort
python scripts/lint.py --tool isort --fix

# Check style with Flake8
python scripts/lint.py --tool flake8

# Type check with MyPy
python scripts/lint.py --tool mypy

# Run all checks and fix what can be fixed
python scripts/lint.py --fix

# Check only (CI mode)
python scripts/lint.py --check-only
```

### Pre-commit Hooks

Once set up, pre-commit hooks run automatically on `git commit`. To run manually:

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files

# Update hooks
pre-commit autoupdate
```

### Manual Commands

You can also run tools directly:

```bash
# Black formatting
black .

# Import sorting
isort .

# Style checking
flake8

# Type checking
mypy

# All tools in sequence
black . && isort . && flake8 && mypy
```

## Error Prevention

This linting setup would catch common issues including:

### F-string Syntax Errors
- **Flake8** catches malformed f-strings like `f"Value: {variable_name"` (missing closing brace)
- **Black** formats f-strings consistently
- **MyPy** validates f-string expressions

### Import Issues
- **isort** ensures consistent import ordering
- **Flake8** catches unused imports and import style issues
- **MyPy** validates imported types

### Code Style Issues
- **Black** enforces consistent formatting
- **Flake8** catches style violations (line length, spacing, etc.)
- **Pre-commit** prevents committing poorly formatted code

### Type Issues
- **MyPy** catches type mismatches and missing type annotations
- **Flake8** catches some basic type-related issues

## Integration with Development Workflow

### VS Code Integration
The project includes VS Code settings for automatic linting:
- Format on save with Black
- Import sorting on save
- Real-time error checking

### CI/CD Integration
For continuous integration:
```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run linting in check mode
python scripts/lint.py --check-only

# Exit with error code if linting fails
exit $?
```

### Git Workflow
With pre-commit hooks enabled:
1. Make changes
2. Stage files: `git add .`
3. Commit: `git commit -m "message"`
4. Pre-commit automatically runs linting
5. Fix any issues if prompted
6. Commit again

## Troubleshooting

### Common Issues

**"Command not found" errors:**
```bash
# Install development dependencies
python scripts/setup_linting.py --dev

# Or manually
pip install -r requirements-dev.txt
```

**Pre-commit hooks failing:**
```bash
# Update pre-commit
pre-commit autoupdate

# Reinstall hooks
pre-commit install --overwrite

# Run specific failing hook
pre-commit run <hook-name> --all-files
```

**MyPy type errors:**
```bash
# Add type ignore comment
variable_name: Any  # type: ignore

# Or fix the type annotation
variable_name: str
```

**Flake8 false positives:**
```python
# Ignore specific line
result = "x" * 100  # noqa: E501

# Or configure in .flake8
```

### Performance Issues

For large codebases, you can:
- Run tools on specific files: `black path/to/file.py`
- Use pre-commit selective runs: `pre-commit run black --files path/to/file.py`
- Exclude files in configuration

## Configuration Customization

### Adjusting Line Length
Edit `.flake8` and `pyproject.toml`:
```ini
# .flake8
max-line-length = 100

[tool.black]
line-length = 100
```

### Excluding Files
Add to `.flake8`:
```ini
exclude =
    .git,
    __pycache__,
    migrations/,
    legacy_module.py
```

### MyPy Strictness
Modify `pyproject.toml`:
```toml
[tool.mypy]
# Less strict
disallow_untyped_defs = false

# More strict
disallow_any_unimported = true
```

## Best Practices

1. **Run linting before committing**
2. **Fix linting errors promptly**
3. **Use type hints for better error catching**
4. **Keep configuration files up to date**
5. **Review pre-commit output regularly**
6. **Don't ignore too many linting errors**

## Migration from Other Tools

If migrating from other linting setups:

1. **Backup existing configuration**
2. **Run new tools in check-only mode first**
3. **Gradually fix issues**
4. **Update team documentation**
5. **Train team members on new workflow**

## Support

For issues with the linting setup:
1. Check the troubleshooting section
2. Validate tool installation
3. Review configuration files
4. Check for tool updates
5. Consult tool documentation

The linting setup ensures consistent, high-quality Python code across the entire project while catching common errors before they reach production.