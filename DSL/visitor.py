from DSL.Robotics.RoboticsParser import RoboticsParser
from DSL.Robotics.RoboticsVisitor import RoboticsVisitor
from DSL.metamodel import Model, Component, Connection
from datetime import timedelta


class ASTBuilder(RoboticsVisitor):
    def __init__(self):
        self.model = Model()

    # componentDecl : COMPONENT ID LBRACE componentBody RBRACE ;
    def visitComponentDecl(self, ctx:RoboticsParser.ComponentDeclContext):
        name = ctx.ID().getText()
        comp = Component(name)
        for attrCtx in ctx.componentBody().componentAttr():
            match attrCtx.start.type:
                case RoboticsParser.PERIOD: comp.period = self._duration(attrCtx)
                case RoboticsParser.DEADLINE: comp.deadline = self._duration(attrCtx)
                case RoboticsParser.WCET: comp.wcet = self._duration(attrCtx)
        self.model.components[name] = comp
        return None                           # do not recurse further

    # connectDecl : CONNECT ID DOT ID ARROW ID DOT ID SEMI ;
    def visitConnectDecl(self, ctx: RoboticsParser.ConnectDeclContext):
        src_ctx = ctx.endpoint(0)
        dst_ctx = ctx.endpoint(1)

        src_comp = src_ctx.comp.text  # label from the grammar
        src_port = src_ctx.port.text
        dst_comp = dst_ctx.comp.text
        dst_port = dst_ctx.port.text
        self.model.connections.append(
            Connection(f"{src_comp}.{src_port}", f"{dst_comp}.{dst_port}")
        )
        return None

    # propertyDecl : PROPERTY ID COLON STRING SEMI ;
    def visitPropertyDecl(self, ctx: RoboticsParser.PropertyDeclContext):
        prop_id = ctx.ID().getText()
        text = ctx.STRING().getText()
        # strip surrounding quotes
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
        self.model.properties[prop_id] = text
        return None

    # helper
    def _duration(self, attrCtx):
        value = int(attrCtx.duration().INT().getText())
        unit = attrCtx.duration().UNIT_MS().getText()  # grammar allows only ms

        return timedelta(milliseconds=value)
