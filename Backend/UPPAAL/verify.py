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
    props = getattr(model.optimisation, "constraints", [])
    results = verifier.check(model, props, xml_out="model.xml")
    for prop, res in results.items():
        print(f"{prop}: {res}")


if __name__ == "__main__":
    file = r"C:/Users/kaiwe/Documents/Master/Masterarbeit/Projekt/DSL/Input/1.adsl"
    main(file)
