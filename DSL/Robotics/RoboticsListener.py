# Generated from C:/Users/kaiwe/Documents/Master/Masterarbeit/Projekt/DSL/Robotics.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .RoboticsParser import RoboticsParser
else:
    from RoboticsParser import RoboticsParser

# This class defines a complete listener for a parse tree produced by RoboticsParser.
class RoboticsListener(ParseTreeListener):

    # Enter a parse tree produced by RoboticsParser#file.
    def enterFile(self, ctx:RoboticsParser.FileContext):
        pass

    # Exit a parse tree produced by RoboticsParser#file.
    def exitFile(self, ctx:RoboticsParser.FileContext):
        pass


    # Enter a parse tree produced by RoboticsParser#statement.
    def enterStatement(self, ctx:RoboticsParser.StatementContext):
        pass

    # Exit a parse tree produced by RoboticsParser#statement.
    def exitStatement(self, ctx:RoboticsParser.StatementContext):
        pass


    # Enter a parse tree produced by RoboticsParser#componentDecl.
    def enterComponentDecl(self, ctx:RoboticsParser.ComponentDeclContext):
        pass

    # Exit a parse tree produced by RoboticsParser#componentDecl.
    def exitComponentDecl(self, ctx:RoboticsParser.ComponentDeclContext):
        pass


    # Enter a parse tree produced by RoboticsParser#componentBody.
    def enterComponentBody(self, ctx:RoboticsParser.ComponentBodyContext):
        pass

    # Exit a parse tree produced by RoboticsParser#componentBody.
    def exitComponentBody(self, ctx:RoboticsParser.ComponentBodyContext):
        pass


    # Enter a parse tree produced by RoboticsParser#componentAttr.
    def enterComponentAttr(self, ctx:RoboticsParser.ComponentAttrContext):
        pass

    # Exit a parse tree produced by RoboticsParser#componentAttr.
    def exitComponentAttr(self, ctx:RoboticsParser.ComponentAttrContext):
        pass


    # Enter a parse tree produced by RoboticsParser#connectDecl.
    def enterConnectDecl(self, ctx:RoboticsParser.ConnectDeclContext):
        pass

    # Exit a parse tree produced by RoboticsParser#connectDecl.
    def exitConnectDecl(self, ctx:RoboticsParser.ConnectDeclContext):
        pass


    # Enter a parse tree produced by RoboticsParser#connectBody.
    def enterConnectBody(self, ctx:RoboticsParser.ConnectBodyContext):
        pass

    # Exit a parse tree produced by RoboticsParser#connectBody.
    def exitConnectBody(self, ctx:RoboticsParser.ConnectBodyContext):
        pass


    # Enter a parse tree produced by RoboticsParser#endpoint.
    def enterEndpoint(self, ctx:RoboticsParser.EndpointContext):
        pass

    # Exit a parse tree produced by RoboticsParser#endpoint.
    def exitEndpoint(self, ctx:RoboticsParser.EndpointContext):
        pass


    # Enter a parse tree produced by RoboticsParser#propertyDecl.
    def enterPropertyDecl(self, ctx:RoboticsParser.PropertyDeclContext):
        pass

    # Exit a parse tree produced by RoboticsParser#propertyDecl.
    def exitPropertyDecl(self, ctx:RoboticsParser.PropertyDeclContext):
        pass


    # Enter a parse tree produced by RoboticsParser#duration.
    def enterDuration(self, ctx:RoboticsParser.DurationContext):
        pass

    # Exit a parse tree produced by RoboticsParser#duration.
    def exitDuration(self, ctx:RoboticsParser.DurationContext):
        pass



del RoboticsParser