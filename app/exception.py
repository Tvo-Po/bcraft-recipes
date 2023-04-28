class InvalidImagesError(Exception):
    def __init__(self, info: list[tuple[int, str | None]]) -> None:
        self.info = info
        string_errors = [
            f'\t{pos}: {name if name else "unnamed"}\n' for pos, name in info
        ]
        super().__init__(f"Invalid images (\n{''.join(string_errors)})")
