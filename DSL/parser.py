from antlr4 import InputStream, CommonTokenStream
from antlr4.tree.Tree import ParseTree
from pathlib import Path

from Robotics.RoboticsLexer import RoboticsLexer
from Robotics.RoboticsParser import RoboticsParser
from visitor import ASTBuilder
from metamodel import Model


def parse_source(text: str) -> ParseTree:
    stream = InputStream(text)
    lexer = RoboticsLexer(stream)
    tokens = CommonTokenStream(lexer)
    parser = RoboticsParser(tokens)
    tree = parser.file_()          # entry rule in the grammar
    if parser.getNumberOfSyntaxErrors():
        raise SyntaxError("input not valid DSL")
    return tree


if __name__ == "__main__":
    dsl_path = Path(r"C:/Users/kaiwe/Documents/Master/Masterarbeit/Projekt/DSL/Input/1.adsl")
    source = dsl_path.read_text(encoding="utf-8")
    tree = parse_source(source)
    builder = ASTBuilder()
    builder.visit(tree)
    model: Model = builder.model
