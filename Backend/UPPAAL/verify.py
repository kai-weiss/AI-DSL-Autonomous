from pathlib import Path
from DSL.parser import parse_source, ASTBuilder
from Backend.UPPAAL.UppaalVerifier import UppaalVerifier


def main(dsl_file: str):
    path = Path(dsl_file)
    source = path.read_text(encoding="utf-8")
    tree = parse_source(source)
    builder = ASTBuilder()
    builder.visit(tree)
    model = builder.model
    verifier = UppaalVerifier()
    props = list(model.properties.keys())
    results = verifier.check(model, props)
    for prop, res in results.items():
        print(f"{prop}: {res}")


if __name__ == "__main__":
    import sys
    file = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).parent/"DSL"/"Input"/"1.adsl")
    main(file)
