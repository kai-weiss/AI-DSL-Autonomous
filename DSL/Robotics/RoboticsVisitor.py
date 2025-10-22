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


    # Visit a parse tree produced by RoboticsParser#propertyString.
    def visitPropertyString(self, ctx:RoboticsParser.PropertyStringContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#propertyBlock.
    def visitPropertyBlock(self, ctx:RoboticsParser.PropertyBlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#vehicleDecl.
    def visitVehicleDecl(self, ctx:RoboticsParser.VehicleDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#cpuDecl.
    def visitCpuDecl(self, ctx:RoboticsParser.CpuDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#cpuAttr.
    def visitCpuAttr(self, ctx:RoboticsParser.CpuAttrContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#classHierarchy.
    def visitClassHierarchy(self, ctx:RoboticsParser.ClassHierarchyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#systemDecl.
    def visitSystemDecl(self, ctx:RoboticsParser.SystemDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#propertyField.
    def visitPropertyField(self, ctx:RoboticsParser.PropertyFieldContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#propertyValue.
    def visitPropertyValue(self, ctx:RoboticsParser.PropertyValueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#dottedId.
    def visitDottedId(self, ctx:RoboticsParser.DottedIdContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#duration.
    def visitDuration(self, ctx:RoboticsParser.DurationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#optimisationBlock.
    def visitOptimisationBlock(self, ctx:RoboticsParser.OptimisationBlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#variableDecl.
    def visitVariableDecl(self, ctx:RoboticsParser.VariableDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#componentRef.
    def visitComponentRef(self, ctx:RoboticsParser.ComponentRefContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#connectionRefWrapped.
    def visitConnectionRefWrapped(self, ctx:RoboticsParser.ConnectionRefWrappedContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#connectionRef.
    def visitConnectionRef(self, ctx:RoboticsParser.ConnectionRefContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#attrName.
    def visitAttrName(self, ctx:RoboticsParser.AttrNameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#rangeSpec.
    def visitRangeSpec(self, ctx:RoboticsParser.RangeSpecContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#objectiveDecl.
    def visitObjectiveDecl(self, ctx:RoboticsParser.ObjectiveDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#constraintDecl.
    def visitConstraintDecl(self, ctx:RoboticsParser.ConstraintDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#literalDuration.
    def visitLiteralDuration(self, ctx:RoboticsParser.LiteralDurationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#addSubExpr.
    def visitAddSubExpr(self, ctx:RoboticsParser.AddSubExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#compExpr.
    def visitCompExpr(self, ctx:RoboticsParser.CompExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#logicExpr.
    def visitLogicExpr(self, ctx:RoboticsParser.LogicExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#atomExpr.
    def visitAtomExpr(self, ctx:RoboticsParser.AtomExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#mulDivExpr.
    def visitMulDivExpr(self, ctx:RoboticsParser.MulDivExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#intLit.
    def visitIntLit(self, ctx:RoboticsParser.IntLitContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#durLit.
    def visitDurLit(self, ctx:RoboticsParser.DurLitContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#varRef.
    def visitVarRef(self, ctx:RoboticsParser.VarRefContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by RoboticsParser#parenExpr.
    def visitParenExpr(self, ctx:RoboticsParser.ParenExprContext):
        return self.visitChildren(ctx)



del RoboticsParser