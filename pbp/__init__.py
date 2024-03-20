def get_pbp_version() -> str:
    try:
        import importlib.metadata

        return importlib.metadata.version("mbari-pbp")
    except Exception:  # pylint: disable=broad-exception-caught
        try:
            from poetry.core.factory import Factory

            factory = Factory()
            poetry = factory.create_poetry()
            return poetry.package.version.text
        except Exception:  # pylint: disable=broad-exception-caught
            return "version not found"


def get_pypam_version() -> str:
    try:
        import importlib.metadata

        return importlib.metadata.version("lifewatch-pypam")
    except Exception:  # pylint: disable=broad-exception-caught
        return "??"
