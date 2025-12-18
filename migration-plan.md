# Narwhals Migration Plan

## Scope
- 91 files import pandas
- ~395 pandas operations to convert
- Keep pandas in tests for now

## Strategy
Work module by module, test and commit after each:

### Phase 1: Core Utilities (HIGH PRIORITY)
- [x] _utils/__init__.py - Core data manipulation utilities
- [ ] layer.py - Layer data handling
- [ ] ggplot.py - Main ggplot class

### Phase 2: Statistics (MEDIUM PRIORITY)
- [ ] stats/stat.py - Base stat class
- [ ] stats/binning.py - Binning operations
- [ ] All stat_*.py files

### Phase 3: Geometries (MEDIUM PRIORITY)
- [ ] geoms/geom.py - Base geom class
- [ ] All geom_*.py files

### Phase 4: Scales & Facets (LOWER PRIORITY)
- [ ] scales/*.py
- [ ] facets/*.py

### Phase 5: Remaining modules
- [ ] mapping/*.py
- [ ] Other utilities

## Testing Strategy
- Run relevant tests after each file
- Run full test suite after each phase
- Commit after each working unit

## Key Conversions
- `pd.DataFrame` → narwhals DataFrame
- `df.copy()` → `df.clone()`
- `df.groupby()` → `df.group_by()`
- `pd.concat()` → `nw.concat()`
- `len(df) == 0` → `df.is_empty()`
- `df.to_native()` to get back to pandas when needed
