---
name: python-testing
version: "1.0"
description: TDD workflow and data science testing patterns for pytest — DataFrame testing, model fixtures, validation, and reproducibility. Generic pytest knowledge is omitted (Claude already knows it).
---

# Python Testing — Team Patterns

TDD workflow and data science-specific testing patterns. Claude already knows pytest basics (fixtures, parametrize, mocking, markers) — this skill covers what's specific to our data science work.

## When to Activate

- Writing new features (follow TDD: red, green, refactor)
- Writing tests for data pipelines, models, or DataFrame transformations
- Reviewing test coverage for data science code

## TDD Cycle

Always follow: **RED** (write failing test) → **GREEN** (minimal code to pass) → **REFACTOR** (improve while green). Target 80%+ coverage.

## Data Science Testing Patterns

### DataFrame Fixtures

```python
@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "feature_1": [1.0, 2.0, 3.0, 4.0, 5.0],
        "feature_2": ["a", "b", "c", "d", "e"],
        "target": [0, 1, 0, 1, 0],
    })

@pytest.fixture
def trained_model(sample_df):
    from sklearn.tree import DecisionTreeClassifier
    X = sample_df[["feature_1"]]
    y = sample_df["target"]
    model = DecisionTreeClassifier(random_state=42)
    model.fit(X, y)
    return model
```

### Testing DataFrames

```python
import pandas.testing as tm

def test_feature_engineering():
    input_df = pd.DataFrame({"price": [100, 200], "quantity": [2, 3]})
    result = add_total_column(input_df)
    expected = pd.DataFrame({
        "price": [100, 200],
        "quantity": [2, 3],
        "total": [200, 600],
    })
    tm.assert_frame_equal(result, expected)
```

### Testing Model Outputs

```python
def test_model_predictions_shape(trained_model, sample_df):
    X = sample_df[["feature_1"]]
    predictions = trained_model.predict(X)
    assert predictions.shape == (len(X),)
    assert set(predictions).issubset({0, 1})

def test_model_reproducibility(sample_df):
    model_1 = train_model(sample_df, random_state=42)
    model_2 = train_model(sample_df, random_state=42)
    X = sample_df[["feature_1"]]
    assert (model_1.predict(X) == model_2.predict(X)).all()
```

### Testing Data Validation

```python
class TestDataValidation:
    def test_valid_dataframe_passes(self, sample_df):
        result = validate_dataframe(sample_df)
        assert result.is_valid is True

    def test_missing_required_column_fails(self, sample_df):
        df = sample_df.drop(columns=["target"])
        result = validate_dataframe(df)
        assert result.is_valid is False

    def test_empty_dataframe_fails(self):
        result = validate_dataframe(pd.DataFrame())
        assert result.is_valid is False
```

## Rules

- **Test behavior, not internals** — `assert model.predict(X).shape == (10,)` not `assert model._n_estimators == 100`
- **Independent tests** — each test sets up its own data, no shared mutable state
- **Always set random seeds** — `random_state=42` for reproducibility
- **Test edge cases** — None, empty DataFrame, NaN, inf, zero, negative values
- **Mock external APIs** — never hit real Jira/Gemini/LDAP in unit tests
