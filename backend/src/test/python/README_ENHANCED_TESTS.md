# Enhanced Dynamic Optimization Tests

## Overview

The enhanced dynamic portfolio optimization test suite provides two levels of testing:

### 🚀 **Simple Tests** (Default - Fast Execution)
- **Purpose**: Quick validation for development and CI/CD
- **Execution Time**: ~10-15 seconds
- **Assets**: 2 assets (AAPL, MSFT) 
- **Data Size**: 15-30 days
- **Configuration**: Minimal parameters (2 generations, 4 population, 1-bit resolution)

### 🔬 **Complex Tests** (On-Demand - Comprehensive Validation)
- **Purpose**: Production-ready validation with realistic scenarios
- **Execution Time**: Several minutes
- **Assets**: 3-4 assets with realistic correlations
- **Data Size**: 90-120 days with market dynamics
- **Configuration**: Full parameters (3-8 generations, 8-16 population, 2-bit resolution)

## Usage Commands

### Run Simple Tests (Default)
```bash
# Via pytest (recommended)
python -m pytest test_enhanced_dynamic_optimization.py

# Direct execution
python test_enhanced_dynamic_optimization.py

# Run only simple tests, skip complex ones
python -m pytest test_enhanced_dynamic_optimization.py -m "not complex"
```

### Run Complex Tests (On Demand)
```bash
# Via pytest marker
python -m pytest test_enhanced_dynamic_optimization.py -m complex

# Direct execution with confirmation
python test_enhanced_dynamic_optimization.py complex

# Show complex tests without running
python -m pytest test_enhanced_dynamic_optimization.py -m complex --collect-only
```

### Run Specific Test Categories
```bash
# Individual test functions
python -m pytest test_enhanced_dynamic_optimization.py::test_basic_optimization
python -m pytest test_enhanced_dynamic_optimization.py::test_complex_basic_optimization

# Performance tests only
python -m pytest test_enhanced_dynamic_optimization.py -k "performance"
```

## Test Structure

### Simple Tests (Always Run)
1. **test_basic_optimization()** - Basic 2-asset optimization
2. **test_qubo_construction()** - QUBO matrix validation 
3. **test_transaction_cost_modeling()** - Cost impact verification
4. **test_api_integration()** - REST API endpoint testing
5. **test_performance_comparison()** - Minimal performance benchmark

### Complex Tests (On-Demand Only)
1. **test_complex_basic_optimization()** - 3-asset realistic optimization
2. **test_complex_transaction_cost_modeling()** - Advanced cost scenarios
3. **test_complex_performance_comparison()** - Comprehensive benchmarks

## Integration with CI/CD

The test suite is designed for efficient CI/CD integration:

- **Default behavior**: Only simple tests run (fast feedback)
- **Complex tests**: Marked with `@pytest.mark.skip` by default
- **On-demand execution**: Use specific markers or arguments
- **No accidental slowdowns**: Complex tests never run unless explicitly requested

## Configuration Files

- **pytest.ini**: Registers the `complex` marker
- **Test markers**: Simple tests have no markers, complex tests use `@pytest.mark.complex`

## Performance Expectations

| Test Type | Duration | CPU Usage | Memory Usage | Quantum Jobs |
|-----------|----------|-----------|--------------|--------------|
| Simple    | 10-15s   | Low       | ~100MB       | 2-5 jobs     |
| Complex   | 2-5min   | High      | ~500MB       | 10-30 jobs   |

This design ensures fast development cycles while maintaining the ability to perform comprehensive validation when needed.