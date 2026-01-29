# Contributing to ephys_compression_tests

This guide explains how to contribute new algorithms or datasets to ephys_compression_tests.

## Overview

ephys_compression_tests welcomes contributions of new compression algorithms and ephys datasets. The framework is designed to make it easy to add new components while ensuring consistent benchmarking and evaluation.

## Getting Started

1. Fork and clone the repository:
```bash
git clone https://github.com/[your-username]/ephys_compression_tests.git
cd ephys_compression_tests
```

2. Install dependencies:
```bash
# Install Python package
cd ephys_compression_tests
pip install -e .

# Install pre-commit hooks for code compliance checks
pip install pre-commit
pre-commit install
```

## Adding a New Algorithm

New algorithms are added in `ephys_compression_tests/src/ephys_compression_tests/algorithms/`. Each algorithm should:

1. Create a new directory with:
   - `__init__.py`: Algorithm implementation
   - `algorithm-name.md`: Documentation and description

2. In `__init__.py`:
   - Implement compression/decompression functions
   - Define metadata (version, tags, compatibility)
   - Follow existing algorithms as examples

Example structure:
```
algorithms/
└── my_algorithm/
    ├── __init__.py
    └── my_algorithm.md
```

## Adding a New Dataset

New datasets are added in `ephys_compression_tests/src/ephys_compression_tests/datasets/`. Each dataset should:

1. Create a new directory with:
   - `__init__.py`: Dataset generation/loading code
   - `dataset-name.md`: Documentation and description

2. In `__init__.py`:
   - Implement data generation/loading
   - Define metadata (version, tags)
   - Follow existing datasets as examples

Example structure:
```
datasets/
└── my_dataset/
    ├── __init__.py
    └── my_dataset.md
```

## Testing Locally

Run benchmarks for your new component:
```bash
ephys_compression_tests run --algorithm my_algorithm --dataset my_dataset
```

The framework will automatically:
- Run the benchmarks
- Verify results by decompressing and comparing with original data
- Measure compression ratios and throughput

## Code Formatting

The project uses specific formatters for each language:
- Python: black formatter
- TypeScript/JavaScript: ESLint + Prettier
- C++: clang-format

To format your code before committing:
```bash
# From project root
./devel/format_code.sh
```

This will format all code according to project standards.

## Code Compliance

Pre-commit hooks will check code compliance when you commit changes. They verify:
- Code formatting
- Import ordering
- Type checking
- Other project-specific rules

If checks fail, format your code using the format script and try again.

## Creating a Pull Request

1. Create a new branch:
```bash
git checkout -b add-my-component
```

2. Format code and ensure it passes compliance checks:
```bash
./devel/format_code.sh
```

3. Commit your changes:
```bash
git add .
git commit -m "Add new algorithm/dataset: [name]"
```

4. Push to your fork:
```bash
git push origin add-my-component
```

5. Open a pull request on GitHub with:
   - Clear description of the new component
   - Any relevant background or references
   - Local benchmark results
   - Confirmation that code is formatted and passes checks

## Guidelines

- Follow existing code structure and patterns
- Include thorough documentation
- Add appropriate tags for filtering
- Test compatibility with existing components
- Format code using provided script
- Ensure all pre-commit checks pass
