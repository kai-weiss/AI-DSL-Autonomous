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


    # Enter a parse tree produced by RoboticsParser#propertyString.
    def enterPropertyString(self, ctx:RoboticsParser.PropertyStringContext):
        pass

    # Exit a parse tree produced by RoboticsParser#propertyString.
    def exitPropertyString(self, ctx:RoboticsParser.PropertyStringContext):
        pass


    # Enter a parse tree produced by RoboticsParser#propertyBlock.
    def enterPropertyBlock(self, ctx:RoboticsParser.PropertyBlockContext):
        pass

    # Exit a parse tree produced by RoboticsParser#propertyBlock.
    def exitPropertyBlock(self, ctx:RoboticsParser.PropertyBlockContext):
        pass


    # Enter a parse tree produced by RoboticsParser#vehicleDecl.
    def enterVehicleDecl(self, ctx:RoboticsParser.VehicleDeclContext):
        pass

    # Exit a parse tree produced by RoboticsParser#vehicleDecl.
    def exitVehicleDecl(self, ctx:RoboticsParser.VehicleDeclContext):
        pass


    # Enter a parse tree produced by RoboticsParser#cpuDecl.
    def enterCpuDecl(self, ctx:RoboticsParser.CpuDeclContext):
        pass

    # Exit a parse tree produced by RoboticsParser#cpuDecl.
    def exitCpuDecl(self, ctx:RoboticsParser.CpuDeclContext):
        pass


    # Enter a parse tree produced by RoboticsParser#cpuAttr.
    def enterCpuAttr(self, ctx:RoboticsParser.CpuAttrContext):
        pass

    # Exit a parse tree produced by RoboticsParser#cpuAttr.
    def exitCpuAttr(self, ctx:RoboticsParser.CpuAttrContext):
        pass


    # Enter a parse tree produced by RoboticsParser#classHierarchy.
    def enterClassHierarchy(self, ctx:RoboticsParser.ClassHierarchyContext):
        pass

    # Exit a parse tree produced by RoboticsParser#classHierarchy.
    def exitClassHierarchy(self, ctx:RoboticsParser.ClassHierarchyContext):
        pass


    # Enter a parse tree produced by RoboticsParser#systemDecl.
    def enterSystemDecl(self, ctx:RoboticsParser.SystemDeclContext):
        pass

    # Exit a parse tree produced by RoboticsParser#systemDecl.
    def exitSystemDecl(self, ctx:RoboticsParser.SystemDeclContext):
        pass


    # Enter a parse tree produced by RoboticsParser#propertyField.
    def enterPropertyField(self, ctx:RoboticsParser.PropertyFieldContext):
        pass

    # Exit a parse tree produced by RoboticsParser#propertyField.
    def exitPropertyField(self, ctx:RoboticsParser.PropertyFieldContext):
        pass


    # Enter a parse tree produced by RoboticsParser#propertyValue.
    def enterPropertyValue(self, ctx:RoboticsParser.PropertyValueContext):
        pass

    # Exit a parse tree produced by RoboticsParser#propertyValue.
    def exitPropertyValue(self, ctx:RoboticsParser.PropertyValueContext):
        pass


    # Enter a parse tree produced by RoboticsParser#dottedId.
    def enterDottedId(self, ctx:RoboticsParser.DottedIdContext):
        pass

    # Exit a parse tree produced by RoboticsParser#dottedId.
    def exitDottedId(self, ctx:RoboticsParser.DottedIdContext):
        pass


    # Enter a parse tree produced by RoboticsParser#duration.
    def enterDuration(self, ctx:RoboticsParser.DurationContext):
        pass

    # Exit a parse tree produced by RoboticsParser#duration.
    def exitDuration(self, ctx:RoboticsParser.DurationContext):
        pass


    # Enter a parse tree produced by RoboticsParser#optimisationBlock.
    def enterOptimisationBlock(self, ctx:RoboticsParser.OptimisationBlockContext):
        pass

    # Exit a parse tree produced by RoboticsParser#optimisationBlock.
    def exitOptimisationBlock(self, ctx:RoboticsParser.OptimisationBlockContext):
        pass


    # Enter a parse tree produced by RoboticsParser#variableDecl.
    def enterVariableDecl(self, ctx:RoboticsParser.VariableDeclContext):
        pass

    # Exit a parse tree produced by RoboticsParser#variableDecl.
    def exitVariableDecl(self, ctx:RoboticsParser.VariableDeclContext):
        pass


    # Enter a parse tree produced by RoboticsParser#componentRef.
    def enterComponentRef(self, ctx:RoboticsParser.ComponentRefContext):
        pass

    # Exit a parse tree produced by RoboticsParser#componentRef.
    def exitComponentRef(self, ctx:RoboticsParser.ComponentRefContext):
        pass


    # Enter a parse tree produced by RoboticsParser#connectionRefWrapped.
    def enterConnectionRefWrapped(self, ctx:RoboticsParser.ConnectionRefWrappedContext):
        pass

    # Exit a parse tree produced by RoboticsParser#connectionRefWrapped.
    def exitConnectionRefWrapped(self, ctx:RoboticsParser.ConnectionRefWrappedContext):
        pass


    # Enter a parse tree produced by RoboticsParser#connectionRef.
    def enterConnectionRef(self, ctx:RoboticsParser.ConnectionRefContext):
        pass

    # Exit a parse tree produced by RoboticsParser#connectionRef.
    def exitConnectionRef(self, ctx:RoboticsParser.ConnectionRefContext):
        pass


    # Enter a parse tree produced by RoboticsParser#attrName.
    def enterAttrName(self, ctx:RoboticsParser.AttrNameContext):
        pass

    # Exit a parse tree produced by RoboticsParser#attrName.
    def exitAttrName(self, ctx:RoboticsParser.AttrNameContext):
        pass


    # Enter a parse tree produced by RoboticsParser#rangeSpec.
    def enterRangeSpec(self, ctx:RoboticsParser.RangeSpecContext):
        pass

    # Exit a parse tree produced by RoboticsParser#rangeSpec.
    def exitRangeSpec(self, ctx:RoboticsParser.RangeSpecContext):
        pass


    # Enter a parse tree produced by RoboticsParser#objectiveDecl.
    def enterObjectiveDecl(self, ctx:RoboticsParser.ObjectiveDeclContext):
        pass

    # Exit a parse tree produced by RoboticsParser#objectiveDecl.
    def exitObjectiveDecl(self, ctx:RoboticsParser.ObjectiveDeclContext):
        pass


    # Enter a parse tree produced by RoboticsParser#constraintDecl.
    def enterConstraintDecl(self, ctx:RoboticsParser.ConstraintDeclContext):
        pass

    # Exit a parse tree produced by RoboticsParser#constraintDecl.
    def exitConstraintDecl(self, ctx:RoboticsParser.ConstraintDeclContext):
        pass


    # Enter a parse tree produced by RoboticsParser#literalDuration.
    def enterLiteralDuration(self, ctx:RoboticsParser.LiteralDurationContext):
        pass

    # Exit a parse tree produced by RoboticsParser#literalDuration.
    def exitLiteralDuration(self, ctx:RoboticsParser.LiteralDurationContext):
        pass


    # Enter a parse tree produced by RoboticsParser#addSubExpr.
    def enterAddSubExpr(self, ctx:RoboticsParser.AddSubExprContext):
        pass

    # Exit a parse tree produced by RoboticsParser#addSubExpr.
    def exitAddSubExpr(self, ctx:RoboticsParser.AddSubExprContext):
        pass


    # Enter a parse tree produced by RoboticsParser#compExpr.
    def enterCompExpr(self, ctx:RoboticsParser.CompExprContext):
        pass

    # Exit a parse tree produced by RoboticsParser#compExpr.
    def exitCompExpr(self, ctx:RoboticsParser.CompExprContext):
        pass


    # Enter a parse tree produced by RoboticsParser#logicExpr.
    def enterLogicExpr(self, ctx:RoboticsParser.LogicExprContext):
        pass

    # Exit a parse tree produced by RoboticsParser#logicExpr.
    def exitLogicExpr(self, ctx:RoboticsParser.LogicExprContext):
        pass


    # Enter a parse tree produced by RoboticsParser#atomExpr.
    def enterAtomExpr(self, ctx:RoboticsParser.AtomExprContext):
        pass

    # Exit a parse tree produced by RoboticsParser#atomExpr.
    def exitAtomExpr(self, ctx:RoboticsParser.AtomExprContext):
        pass


    # Enter a parse tree produced by RoboticsParser#mulDivExpr.
    def enterMulDivExpr(self, ctx:RoboticsParser.MulDivExprContext):
        pass

    # Exit a parse tree produced by RoboticsParser#mulDivExpr.
    def exitMulDivExpr(self, ctx:RoboticsParser.MulDivExprContext):
        pass


    # Enter a parse tree produced by RoboticsParser#intLit.
    def enterIntLit(self, ctx:RoboticsParser.IntLitContext):
        pass

    # Exit a parse tree produced by RoboticsParser#intLit.
    def exitIntLit(self, ctx:RoboticsParser.IntLitContext):
        pass


    # Enter a parse tree produced by RoboticsParser#durLit.
    def enterDurLit(self, ctx:RoboticsParser.DurLitContext):
        pass

    # Exit a parse tree produced by RoboticsParser#durLit.
    def exitDurLit(self, ctx:RoboticsParser.DurLitContext):
        pass


    # Enter a parse tree produced by RoboticsParser#varRef.
    def enterVarRef(self, ctx:RoboticsParser.VarRefContext):
        pass

    # Exit a parse tree produced by RoboticsParser#varRef.
    def exitVarRef(self, ctx:RoboticsParser.VarRefContext):
        pass


    # Enter a parse tree produced by RoboticsParser#parenExpr.
    def enterParenExpr(self, ctx:RoboticsParser.ParenExprContext):
        pass

    # Exit a parse tree produced by RoboticsParser#parenExpr.
    def exitParenExpr(self, ctx:RoboticsParser.ParenExprContext):
        pass



del RoboticsParser