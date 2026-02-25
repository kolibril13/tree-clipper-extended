from pathlib import Path

from .util import import_and_check


def test_backwards_compatibility_to_0_1_1(file: str):
    file_path = Path(file)

    # once this is done, we can remove this return
    # https://github.com/Algebraic-UG/tree_clipper/issues/171
    if file_path.parent.stem == "CompositorNodeTree":
        return

    import_and_check(import_file=file_path)
