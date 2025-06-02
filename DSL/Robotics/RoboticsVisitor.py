# Generated from C:/Users/kaiwe/Documents/Master/Masterarbeit/Projekt/DSL/Robotics.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .RoboticsParser import RoboticsParser
else:
    from RoboticsParser import RoboticsParser

# This class defines a complete generic visitor for a parse tree produced by RoboticsParser.

class RoboticsVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by RoboticsParser#file.
    def visitFile(self, ctx:RoboticsParser.FileContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#statement.
    def visitStatement(self, ctx:RoboticsParser.StatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#componentDecl.
    def visitComponentDecl(self, ctx:RoboticsParser.ComponentDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#componentBody.
    def visitComponentBody(self, ctx:RoboticsParser.ComponentBodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#componentAttr.
    def visitComponentAttr(self, ctx:RoboticsParser.ComponentAttrContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#connectDecl.
    def visitConnectDecl(self, ctx:RoboticsParser.ConnectDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#connectBody.
    def visitConnectBody(self, ctx:RoboticsParser.ConnectBodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#endpoint.
    def visitEndpoint(self, ctx:RoboticsParser.EndpointContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#propertyDecl.
    def visitPropertyDecl(self, ctx:RoboticsParser.PropertyDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#duration.
    def visitDuration(self, ctx:RoboticsParser.DurationContext):
        return self.visitChildren(ctx)



del RoboticsParser