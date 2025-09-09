# Contributing to ScryptMineOS 🤝

Thank you for your interest in contributing to ScryptMineOS! This document provides guidelines and information for contributors.

## 🎯 Ways to Contribute

### 🐛 Bug Reports
- Use the [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md)
- Include detailed reproduction steps
- Provide system information and logs
- Check existing issues before creating new ones

### 💡 Feature Requests
- Use the [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.md)
- Explain the use case and benefits
- Consider implementation complexity
- Discuss with maintainers before large changes

### 📝 Documentation
- Improve existing documentation
- Add examples and tutorials
- Fix typos and clarify instructions
- Translate documentation to other languages

### 🔧 Code Contributions
- Follow coding standards and style guidelines
- Include comprehensive tests
- Update documentation as needed
- Ensure backward compatibility

## 🛠️ Development Setup

### Prerequisites
```bash
# Required tools
python >= 3.8
git
pre-commit
```

### Local Development
```bash
# Clone the repository
git clone https://github.com/JlovesYouGit/ScryptMineOS.git
cd ScryptMineOS

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install

# Run tests
pytest
```

## 📋 Coding Standards

### Python Style Guide
- Follow [PEP 8](https://pep8.org/) style guidelines
- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Use [flake8](https://flake8.pycqa.org/) for linting

### Code Quality
- Maintain test coverage above 80%
- Write docstrings for all public functions
- Use type hints where appropriate
- Follow SOLID principles

### Example Code Style
```python
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ASICSimulator:
    """Simulates ASIC mining hardware behavior.
    
    Args:
        model: ASIC model identifier
        hashrate: Expected hashrate in MH/s
        power_consumption: Power usage in watts
    """
    
    def __init__(
        self, 
        model: str, 
        hashrate: float, 
        power_consumption: int
    ) -> None:
        self.model = model
        self.hashrate = hashrate
        self.power_consumption = power_consumption
        self._is_running = False
    
    def start_mining(self, pool_url: str) -> bool:
        """Start mining simulation.
        
        Args:
            pool_url: Mining pool connection string
            
        Returns:
            True if simulation started successfully
        """
        logger.info(f"Starting {self.model} simulation")
        # Implementation details...
        return True
```

## 🧪 Testing Guidelines

### Test Structure
```
tests/
├── unit/           # Unit tests for individual components
├── integration/    # Integration tests for component interaction
├── fixtures/       # Test data and fixtures
└── conftest.py     # Pytest configuration
```

### Writing Tests
```python
import pytest
from scryptmineos import ASICSimulator


class TestASICSimulator:
    """Test suite for ASIC simulator."""
    
    def test_initialization(self):
        """Test simulator initialization."""
        sim = ASICSimulator("L3+", 504.0, 800)
        assert sim.model == "L3+"
        assert sim.hashrate == 504.0
        assert sim.power_consumption == 800
    
    def test_start_mining_success(self):
        """Test successful mining start."""
        sim = ASICSimulator("L3+", 504.0, 800)
        result = sim.start_mining("stratum+tcp://pool.example.com:4444")
        assert result is True
    
    @pytest.mark.parametrize("invalid_url", [
        "",
        "invalid-url",
        "http://not-stratum.com"
    ])
    def test_start_mining_invalid_url(self, invalid_url):
        """Test mining start with invalid URLs."""
        sim = ASICSimulator("L3+", 504.0, 800)
        with pytest.raises(ValueError):
            sim.start_mining(invalid_url)
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=scryptmineos --cov-report=html

# Run specific test file
pytest tests/unit/test_simulator.py

# Run tests matching pattern
pytest -k "test_asic"
```

## 📝 Documentation Standards

### Docstring Format
Use Google-style docstrings:

```python
def calculate_profitability(
    hashrate: float, 
    power_cost: float, 
    coin_price: float
) -> Dict[str, float]:
    """Calculate mining profitability metrics.
    
    Args:
        hashrate: Mining hashrate in MH/s
        power_cost: Electricity cost per kWh
        coin_price: Current coin price in USD
        
    Returns:
        Dictionary containing profitability metrics:
        - daily_profit: Profit per day in USD
        - monthly_profit: Profit per month in USD
        - break_even_days: Days to break even
        
    Raises:
        ValueError: If any input parameter is negative
        
    Example:
        >>> metrics = calculate_profitability(504.0, 0.10, 50.0)
        >>> print(f"Daily profit: ${metrics['daily_profit']:.2f}")
        Daily profit: $12.34
    """
```

### README Updates
- Keep examples current and working
- Update feature lists when adding functionality
- Maintain accurate installation instructions
- Include performance benchmarks when relevant

## 🔄 Pull Request Process

### Before Submitting
1. **Fork the repository** and create a feature branch
2. **Write tests** for new functionality
3. **Update documentation** as needed
4. **Run the full test suite** and ensure it passes
5. **Check code style** with pre-commit hooks

### PR Guidelines
- Use descriptive titles and detailed descriptions
- Reference related issues with "Fixes #123" or "Closes #456"
- Include screenshots for UI changes
- Keep PRs focused and reasonably sized
- Respond to review feedback promptly

### PR Template
```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings introduced
```

## 🏷️ Release Process

### Version Numbering
We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist
1. Update version numbers
2. Update CHANGELOG.md
3. Create release notes
4. Tag the release
5. Update documentation
6. Announce the release

## 🤝 Community Guidelines

### Code of Conduct
- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect different viewpoints and experiences

### Communication Channels
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and community chat
- **Pull Requests**: Code review and collaboration

### Getting Help
- Check existing documentation and issues first
- Provide detailed information when asking questions
- Be patient and respectful when seeking help
- Help others when you can

## 🎖️ Recognition

Contributors are recognized in:
- **CONTRIBUTORS.md**: All contributors listed
- **Release Notes**: Major contributors highlighted
- **GitHub**: Contributor statistics and graphs

Thank you for contributing to ScryptMineOS! 🚀
