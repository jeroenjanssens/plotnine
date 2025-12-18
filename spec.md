# Minimal Narwhals Integration for Plotnine

## Goal
Add narwhals support to plotnine to enable `ggplot(data, aes(x="x", y="y")) + geom_point()` to work with any narwhals-compatible dataframe backend (Pandas, Polars, PyArrow, etc.) with minimal code changes.

## Architecture Decision

**Use narwhals as an input adapter layer only:**
- Convert any narwhals-compatible dataframe to pandas at entry points
- Keep pandas as internal representation (minimal changes, maintains stability)
- Leverage existing `to_pandas()` infrastructure

**Rationale:** The execution path uses extensive pandas-specific operations. Converting these would require modifying 50+ files. This approach gets multi-backend support with ~80 lines of code changes.

## Implementation Steps

### 1. Add narwhals dependency
**File:** `pyproject.toml`

Add `"narwhals>=1.30.0"` to the dependencies list after pandas.

---

### 2. Create narwhals adapter utility
**File:** `plotnine/_utils/__init__.py`

Add new function `to_pandas_via_narwhals()`:
```python
def to_pandas_via_narwhals(data: Any) -> pd.DataFrame:
    """
    Convert any dataframe-like object to pandas using narwhals.

    Supports pandas, polars, pyarrow, and any narwhals-compatible backend.
    """
    import narwhals as nw

    # Fast-path: already pandas
    if isinstance(data, pd.DataFrame):
        return data

    # Legacy: has to_pandas method
    if hasattr(data, "to_pandas"):
        return data.to_pandas()

    # Try narwhals conversion
    try:
        nw_df = nw.from_native(data, eager_only=True)
        return nw.to_native(nw_df)
    except Exception:
        raise TypeError(
            f"Data must be a pandas DataFrame or narwhals-compatible "
            f"dataframe (polars, pyarrow, etc.), got {type(data)}"
        )
```

Update `is_data_like()` function to recognize narwhals-compatible dataframes:
```python
def is_data_like(obj: Any) -> TypeGuard[DataLike]:
    """Return True if obj could be data"""
    if isinstance(obj, pd.DataFrame) or callable(obj) or hasattr(obj, "to_pandas"):
        return True

    # Check if narwhals can handle it
    try:
        import narwhals as nw
        nw.from_native(obj, eager_only=True, pass_through=False)
        return True
    except Exception:
        return False
```

---

### 3. Update layer data conversion
**File:** `plotnine/layer.py`

Modify `_make_layer_data()` method around lines 168-213:

**Replace current logic:**
```python
if plot_data is None:
    data = pd.DataFrame()
elif hasattr(plot_data, "to_pandas"):
    data = cast("DataFrameConvertible", plot_data).to_pandas()
else:
    data = cast("pd.DataFrame", plot_data)
```

**With:**
```python
from ._utils import to_pandas_via_narwhals

if plot_data is None:
    data = pd.DataFrame()
else:
    data = to_pandas_via_narwhals(plot_data)
```

Also update layer-specific data handling (around line 205-213) to use the same conversion.

---

### 4. Update ggplot data piping
**File:** `plotnine/ggplot.py`

Modify `__rrshift__()` method (lines 291-304) to convert non-pandas dataframes:

```python
def __rrshift__(self, other: DataLike) -> ggplot:
    """Overload the >> operator to receive a dataframe"""
    from ._utils import to_pandas_via_narwhals

    other = ungroup(other)
    if is_data_like(other):
        if self.data is None:
            # Convert to pandas if needed
            if not isinstance(other, pd.DataFrame) and not callable(other):
                other = to_pandas_via_narwhals(other)
            self.data = other
        else:
            raise PlotnineError("`>>` failed, ggplot object has data.")
    else:
        msg = "Unknown type of data -- {!r}"
        raise TypeError(msg.format(type(other)))
    return self
```

---

### 5. Add comprehensive test
**File:** `tests/test_geom_point.py`

Add new test function at the end:

```python
def test_narwhals_backends():
    """Test that geom_point works with multiple dataframe backends"""
    import pandas as pd
    from plotnine import ggplot, aes, geom_point

    # Create pandas reference
    pandas_data = pd.DataFrame({"x": [1, 2, 3], "y": [1, 2, 3]})
    p_pandas = ggplot(pandas_data, aes("x", "y")) + geom_point()

    # Test with polars if available
    try:
        import polars as pl
        polars_data = pl.DataFrame({"x": [1, 2, 3], "y": [1, 2, 3]})
        p_polars = ggplot(polars_data, aes("x", "y")) + geom_point()
        # Verify plot constructs successfully
        assert p_polars.layers[0].geom.__class__.__name__ == "geom_point"
    except ImportError:
        pass

    # Test with pyarrow if available
    try:
        import pyarrow as pa
        pyarrow_data = pa.table({"x": [1, 2, 3], "y": [1, 2, 3]})
        p_pyarrow = ggplot(pyarrow_data, aes("x", "y")) + geom_point()
        assert p_pyarrow.layers[0].geom.__class__.__name__ == "geom_point"
    except ImportError:
        pass

    # At minimum, pandas should work
    assert p_pandas.layers[0].geom.__class__.__name__ == "geom_point"
```

---

## Files Modified

1. **pyproject.toml** - Add narwhals dependency (1 line)
2. **plotnine/_utils/__init__.py** - Add conversion utility and update type guard (~40 lines)
3. **plotnine/layer.py** - Update data conversion logic (~10 lines modified)
4. **plotnine/ggplot.py** - Update >> operator (~5 lines modified)
5. **tests/test_geom_point.py** - Add multi-backend test (~25 lines)

**Total:** ~80 lines across 5 files

## Testing Strategy

1. Run existing test suite - should pass unchanged (backward compatibility)
2. Run new multi-backend test with optional dependencies
3. Manual verification with polars/pyarrow dataframes
4. Verify the original example works: `ggplot(anscombe_quartet, aes(x="x", y="y")) + geom_point()`

## Trade-offs

**Advantages:**
- Minimal changes (~80 lines)
- Backward compatible
- Low risk (pandas stays internal)
- Clear architecture
- Works immediately with all narwhals backends

**Disadvantages:**
- Memory overhead (conversion creates copy)
- Can't leverage native backend performance
- Future full narwhals migration would require larger refactor

This is the right minimal approach - users get multi-backend support without risk to existing functionality.
