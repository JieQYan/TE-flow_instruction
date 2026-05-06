project = "TE-flow"
copyright = "2026"
author = "TE-flow"

extensions = []
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

root_doc = "index"

# Prefer the Read the Docs theme when it is available, otherwise fall back
# to a built-in theme so the docs can still be built in a clean environment.
try:
    import sphinx_rtd_theme  # noqa: F401

    html_theme = "sphinx_rtd_theme"
except Exception:
    html_theme = "alabaster"

html_static_path = ["_static"]
