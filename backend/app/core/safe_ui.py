"""Non-Streamlit compatibility helpers for removed legacy UI wrappers.

These keep old backend imports from failing without reintroducing Streamlit.
They return sanitized defaults for API/non-UI contexts.
"""


def safe_multiselect(label, options, default=None, key=None, **kwargs):
    default = default or []
    return [value for value in default if value in options]


def safe_selectbox(label, options, index=0, key=None, **kwargs):
    if not options:
        return None
    safe_index = index if 0 <= index < len(options) else 0
    return list(options)[safe_index]


def safe_slider(label, min_val, max_val, default, key=None, **kwargs):
    try:
        value = default if min_val <= default <= max_val else min_val
    except TypeError:
        value = min_val
    return value
