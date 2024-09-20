# Publishing mbari-pbp

The [`release-pypi.yml`](.github/workflows/release-pypi.yml) GitHub workflow 
takes care of the actual publishing to PyPI.

We just need to proceed as follows. 

- Make sure all is OK in terms of code formatting, typing, testing, and linting:
    ```
    just all
    ```

- Make sure the desired version is captured in `pyproject.toml` (under `[tool.poetry]`).

- Commit the changes.

- Create and push a corresponding git tag.
  This tag must be of the form `vX.Y.Z` for version `X.Y.Z`.

- That should trigger the release workflow.


--- 

The `tag-and-push` recipe may come in handy as it automates the extracting of the
version from `pyproject.toml`, creating the tag accordingly, and pushing it.
