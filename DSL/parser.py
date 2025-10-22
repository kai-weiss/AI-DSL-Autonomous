from antlr4 import InputStream, CommonTokenStream
from antlr4.tree.Tree import ParseTree
from pathlib import Path

from DSL.Robotics.RoboticsLexer import RoboticsLexer
from DSL.Robotics.RoboticsParser import RoboticsParser
from DSL.visitor import ASTBuilder
from DSL.metamodel import Model


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
    dsl_path = Path(r"C:/Users/kaiwe/Documents/Master/Masterarbeit/Projekt/Data/DSLInput/3.adsl")
    source = dsl_path.read_text(encoding="utf-8")
    tree = parse_source(source)
    builder = ASTBuilder()
    builder.visit(tree)
    model: Model = builder.model
