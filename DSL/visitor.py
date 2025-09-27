from DSL.Robotics.RoboticsParser import RoboticsParser
from DSL.Robotics.RoboticsVisitor import RoboticsVisitor
from DSL.metamodel import Model, Component, Connection, OptimisationSpec, Variable
from datetime import timedelta


class ASTBuilder(RoboticsVisitor):
    def __init__(self):
        self.model = Model()
        self._vehicle_stack: list[str] = []
        self._seen_vehicles: set[str] = set()

    # componentDecl : COMPONENT ID LBRACE componentBody RBRACE ;
    def visitComponentDecl(self, ctx: RoboticsParser.ComponentDeclContext):
        name = ctx.ID().getText()
        comp = Component(name)
        if self._vehicle_stack:
            comp.vehicle = self._vehicle_stack[-1]
            vehicle = comp.vehicle
            if vehicle not in self.model.vehicles:
                self.model.vehicles[vehicle] = []
            self.model.vehicles[vehicle].append(comp.name)
        for attrCtx in ctx.componentBody().componentAttr():
            match attrCtx.start.type:
                case RoboticsParser.PERIOD:
                    comp.period = self._duration(attrCtx)
                case RoboticsParser.DEADLINE:
                    comp.deadline = self._duration(attrCtx)
                case RoboticsParser.WCET:
                    comp.wcet = self._duration(attrCtx)
                case RoboticsParser.PRIORITY:
                    comp.priority = int(attrCtx.INT().getText())
        self.model.components[name] = comp
        return None  # do not recurse further

    # connectDecl : CONNECT ID DOT ID ARROW ID DOT ID SEMI ;
    def visitConnectDecl(self, ctx: RoboticsParser.ConnectDeclContext):
        conn_name = ctx.ID().getText()
        src_ctx = ctx.endpoint(0)
        dst_ctx = ctx.endpoint(1)

        src_comp = src_ctx.dottedId().getText()  # label from the grammar
        src_port = src_ctx.port.text
        dst_comp = dst_ctx.dottedId().getText()
        dst_port = dst_ctx.port.text
        budget = None
        if ctx.connectBody():
            dur = ctx.connectBody().duration()
            ms = int(dur.INT().getText())
            budget = timedelta(milliseconds=ms)

        self.model.connections.append(
            Connection(
                conn_name,
                f"{src_comp}.{src_port}",
                f"{dst_comp}.{dst_port}",
                budget,
            )
        )
        return None

    # propertyDecl : PROPERTY ID COLON STRING SEMI ; (propertyString)
    def visitPropertyString(self, ctx: RoboticsParser.PropertyStringContext):
        prop_id = ctx.ID().getText()
        text = ctx.STRING().getText()
        # strip surrounding quotes
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
        self.model.properties[prop_id] = text
        return None

    # propertyDecl : PROPERTY ID LBRACE propertyField* RBRACE ; (propertyBlock)
    def visitPropertyBlock(self, ctx: RoboticsParser.PropertyBlockContext):
        prop_id = ctx.ID().getText()
        parts = []
        for f in ctx.propertyField():
            key = f.ID().getText()
            valCtx = f.propertyValue()
            if valCtx.duration():
                val = f"{valCtx.duration().INT().getText()}ms"
            else:
                val = valCtx.getText()
            parts.append(f"{key}={val}")
        self.model.properties[prop_id] = '; '.join(parts)
        return None

    # systemDecl : SYSTEM ID LBRACE statement* RBRACE ;
    def visitSystemDecl(self, ctx: RoboticsParser.SystemDeclContext):
        self.model.system_name = ctx.ID().getText()
        for elem in ctx.statement():
            self.visit(elem)
        return None

    # vehicleDecl : VEHICLE ID LBRACE componentDecl* RBRACE ;
    def visitVehicleDecl(self, ctx: RoboticsParser.VehicleDeclContext):
        vehicle_name = ctx.ID().getText()
        if vehicle_name not in self._seen_vehicles:
            self.model.vehicle_order.append(vehicle_name)
            self._seen_vehicles.add(vehicle_name)
        if vehicle_name not in self.model.vehicles:
            self.model.vehicles[vehicle_name] = []
        self._vehicle_stack.append(vehicle_name)
        try:
            for comp in ctx.componentDecl():
                self.visit(comp)
        finally:
            self._vehicle_stack.pop()
        return None

    # cpuDecl : CPU LBRACE cpuAttr* RBRACE ;
    def visitCpuDecl(self, ctx: RoboticsParser.CpuDeclContext):
        for attrCtx in ctx.cpuAttr():
            key = attrCtx.getChild(0).getText()
            value = attrCtx.getChild(2).getText()
            self.model.cpu_attrs.append((key, value))
        return None

    # optimisationBlock : OPTIMISATION '{' VARIABLES '{' variableDecl+ '}'
    def visitOptimisationBlock(self, ctx: RoboticsParser.OptimisationBlockContext):
        spec = OptimisationSpec()
        # VARIABLE declarations
        for varCtx in ctx.variableDecl():
            spec.variables.append(self._variable(varCtx))
        # OBJECTIVE declarations
        for objCtx in ctx.objectiveDecl():
            if objCtx.MINIMISE():
                verb = objCtx.MINIMISE().getText()
            else:
                verb = objCtx.MAXIMISE().getText()
            spec.objectives.append(f"{verb} {objCtx.ID().getText()};")
        # CONSTRAINT declarations
        for conCtx in ctx.constraintDecl():
            # strip leading 'assert ' and trailing ';'
            text = conCtx.getText()
            text = text[len('assert'):].rstrip(';')
            spec.constraints.append(text.strip())
        self.model.optimisation = spec
        return None

    # helper
    def _duration(self, attrCtx):
        value = int(attrCtx.duration().INT().getText())
        unit = attrCtx.duration().UNIT_MS().getText()  # grammar allows only ms

        return timedelta(milliseconds=value)

    def _variable(self, ctx: RoboticsParser.VariableDeclContext) -> Variable:
        """Convert a variableDecl into a class Variable instance"""

        # Resolve target reference
        target = ctx.targetRef()
        if isinstance(target, RoboticsParser.ComponentRefContext):
            ref = target.dottedId().getText()
        else:  # ConnectionRefWrapped
            conn = target.connectionRef()
            src_comp = conn.dottedId(0).getText()
            src_port = conn.ID(0).getText()
            dst_comp = conn.dottedId(1).getText()
            dst_port = conn.ID(1).getText()
            ref = f"({src_comp}.{src_port}->{dst_comp}.{dst_port})"

        attr = ctx.attrName().getText()

        r = ctx.rangeSpec()
        low = int(r.literalDuration(0).INT().getText())
        high = int(r.literalDuration(1).INT().getText())

        return Variable(
            ref=f"{ref}.{attr}",
            lower=timedelta(milliseconds=low),
            upper=timedelta(milliseconds=high),
        )
