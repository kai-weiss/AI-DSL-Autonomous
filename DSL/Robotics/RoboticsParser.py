# Generated from C:/Users/kaiwe/Documents/Master/Masterarbeit/Projekt/DSL/Robotics.g4 by ANTLR 4.13.2
# encoding: utf-8
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
	from typing import TextIO
else:
	from typing.io import TextIO

def serializedATN():
    return [
        4,1,47,295,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,2,4,7,4,2,5,7,5,2,6,7,
        6,2,7,7,7,2,8,7,8,2,9,7,9,2,10,7,10,2,11,7,11,2,12,7,12,2,13,7,13,
        2,14,7,14,2,15,7,15,2,16,7,16,2,17,7,17,2,18,7,18,2,19,7,19,2,20,
        7,20,2,21,7,21,2,22,7,22,2,23,7,23,2,24,7,24,2,25,7,25,2,26,7,26,
        2,27,7,27,1,0,5,0,58,8,0,10,0,12,0,61,9,0,1,0,1,0,1,1,1,1,1,1,1,
        1,1,1,1,1,1,1,3,1,72,8,1,1,2,1,2,1,2,1,2,1,2,1,2,1,3,1,3,1,3,5,3,
        83,8,3,10,3,12,3,86,9,3,1,4,1,4,1,4,1,4,1,4,1,4,1,4,1,4,1,4,1,4,
        1,4,1,4,3,4,100,8,4,1,5,1,5,1,5,3,5,105,8,5,1,5,1,5,1,5,1,5,3,5,
        111,8,5,1,6,1,6,1,6,1,6,1,6,1,6,1,6,1,7,1,7,1,7,1,7,1,8,1,8,1,8,
        1,8,1,8,1,8,1,8,1,8,1,8,5,8,133,8,8,10,8,12,8,136,9,8,1,8,3,8,139,
        8,8,1,9,1,9,1,9,1,9,5,9,145,8,9,10,9,12,9,148,9,9,1,9,1,9,1,10,1,
        10,1,10,5,10,155,8,10,10,10,12,10,158,9,10,1,10,1,10,1,11,1,11,1,
        11,1,11,1,11,1,12,1,12,1,12,1,12,5,12,171,8,12,10,12,12,12,174,9,
        12,1,12,1,12,1,13,1,13,1,13,1,13,1,13,1,14,1,14,1,14,3,14,186,8,
        14,1,15,1,15,1,15,5,15,191,8,15,10,15,12,15,194,9,15,1,16,1,16,1,
        16,1,17,1,17,1,17,1,17,1,17,4,17,204,8,17,11,17,12,17,205,1,17,1,
        17,1,17,1,17,4,17,212,8,17,11,17,12,17,213,1,17,1,17,1,17,1,17,4,
        17,220,8,17,11,17,12,17,221,1,17,1,17,1,17,1,18,1,18,1,18,1,18,1,
        18,1,18,1,18,1,19,1,19,1,19,1,19,1,19,3,19,239,8,19,1,20,1,20,1,
        20,1,20,1,20,1,20,1,20,1,20,1,21,1,21,1,22,1,22,1,22,1,22,1,23,1,
        23,1,23,1,23,1,24,1,24,1,24,1,24,1,25,1,25,1,25,1,26,1,26,1,26,1,
        26,1,26,1,26,1,26,1,26,1,26,1,26,1,26,1,26,1,26,1,26,1,26,5,26,281,
        8,26,10,26,12,26,284,9,26,1,27,1,27,1,27,1,27,1,27,1,27,1,27,3,27,
        293,8,27,1,27,0,1,52,28,0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,
        30,32,34,36,38,40,42,44,46,48,50,52,54,0,7,2,0,23,23,47,47,2,0,7,
        11,47,47,1,0,31,32,1,0,45,46,1,0,43,44,1,0,37,42,1,0,35,36,298,0,
        59,1,0,0,0,2,71,1,0,0,0,4,73,1,0,0,0,6,84,1,0,0,0,8,99,1,0,0,0,10,
        101,1,0,0,0,12,112,1,0,0,0,14,119,1,0,0,0,16,138,1,0,0,0,18,140,
        1,0,0,0,20,151,1,0,0,0,22,161,1,0,0,0,24,166,1,0,0,0,26,177,1,0,
        0,0,28,185,1,0,0,0,30,187,1,0,0,0,32,195,1,0,0,0,34,198,1,0,0,0,
        36,226,1,0,0,0,38,238,1,0,0,0,40,240,1,0,0,0,42,248,1,0,0,0,44,250,
        1,0,0,0,46,254,1,0,0,0,48,258,1,0,0,0,50,262,1,0,0,0,52,265,1,0,
        0,0,54,292,1,0,0,0,56,58,3,2,1,0,57,56,1,0,0,0,58,61,1,0,0,0,59,
        57,1,0,0,0,59,60,1,0,0,0,60,62,1,0,0,0,61,59,1,0,0,0,62,63,5,0,0,
        1,63,1,1,0,0,0,64,72,3,4,2,0,65,72,3,10,5,0,66,72,3,16,8,0,67,72,
        3,34,17,0,68,72,3,24,12,0,69,72,3,18,9,0,70,72,3,20,10,0,71,64,1,
        0,0,0,71,65,1,0,0,0,71,66,1,0,0,0,71,67,1,0,0,0,71,68,1,0,0,0,71,
        69,1,0,0,0,71,70,1,0,0,0,72,3,1,0,0,0,73,74,5,4,0,0,74,75,5,47,0,
        0,75,76,5,16,0,0,76,77,3,6,3,0,77,78,5,17,0,0,78,5,1,0,0,0,79,80,
        3,8,4,0,80,81,5,19,0,0,81,83,1,0,0,0,82,79,1,0,0,0,83,86,1,0,0,0,
        84,82,1,0,0,0,84,85,1,0,0,0,85,7,1,0,0,0,86,84,1,0,0,0,87,88,5,7,
        0,0,88,89,5,20,0,0,89,100,3,32,16,0,90,91,5,8,0,0,91,92,5,20,0,0,
        92,100,3,32,16,0,93,94,5,9,0,0,94,95,5,20,0,0,95,100,3,32,16,0,96,
        97,5,10,0,0,97,98,5,20,0,0,98,100,5,23,0,0,99,87,1,0,0,0,99,90,1,
        0,0,0,99,93,1,0,0,0,99,96,1,0,0,0,100,9,1,0,0,0,101,104,5,5,0,0,
        102,103,5,47,0,0,103,105,5,18,0,0,104,102,1,0,0,0,104,105,1,0,0,
        0,105,106,1,0,0,0,106,107,3,14,7,0,107,108,5,15,0,0,108,110,3,14,
        7,0,109,111,3,12,6,0,110,109,1,0,0,0,110,111,1,0,0,0,111,11,1,0,
        0,0,112,113,5,16,0,0,113,114,5,11,0,0,114,115,5,20,0,0,115,116,3,
        32,16,0,116,117,5,19,0,0,117,118,5,17,0,0,118,13,1,0,0,0,119,120,
        3,30,15,0,120,121,5,21,0,0,121,122,5,47,0,0,122,15,1,0,0,0,123,124,
        5,6,0,0,124,125,5,47,0,0,125,126,5,18,0,0,126,127,5,22,0,0,127,139,
        5,19,0,0,128,129,5,6,0,0,129,130,5,47,0,0,130,134,5,16,0,0,131,133,
        3,26,13,0,132,131,1,0,0,0,133,136,1,0,0,0,134,132,1,0,0,0,134,135,
        1,0,0,0,135,137,1,0,0,0,136,134,1,0,0,0,137,139,5,17,0,0,138,123,
        1,0,0,0,138,128,1,0,0,0,139,17,1,0,0,0,140,141,5,13,0,0,141,142,
        5,47,0,0,142,146,5,16,0,0,143,145,3,4,2,0,144,143,1,0,0,0,145,148,
        1,0,0,0,146,144,1,0,0,0,146,147,1,0,0,0,147,149,1,0,0,0,148,146,
        1,0,0,0,149,150,5,17,0,0,150,19,1,0,0,0,151,152,5,14,0,0,152,156,
        5,16,0,0,153,155,3,22,11,0,154,153,1,0,0,0,155,158,1,0,0,0,156,154,
        1,0,0,0,156,157,1,0,0,0,157,159,1,0,0,0,158,156,1,0,0,0,159,160,
        5,17,0,0,160,21,1,0,0,0,161,162,5,47,0,0,162,163,5,20,0,0,163,164,
        7,0,0,0,164,165,5,19,0,0,165,23,1,0,0,0,166,167,5,12,0,0,167,168,
        5,47,0,0,168,172,5,16,0,0,169,171,3,2,1,0,170,169,1,0,0,0,171,174,
        1,0,0,0,172,170,1,0,0,0,172,173,1,0,0,0,173,175,1,0,0,0,174,172,
        1,0,0,0,175,176,5,17,0,0,176,25,1,0,0,0,177,178,5,47,0,0,178,179,
        5,20,0,0,179,180,3,28,14,0,180,181,5,19,0,0,181,27,1,0,0,0,182,186,
        3,32,16,0,183,186,3,30,15,0,184,186,5,47,0,0,185,182,1,0,0,0,185,
        183,1,0,0,0,185,184,1,0,0,0,186,29,1,0,0,0,187,192,5,47,0,0,188,
        189,5,21,0,0,189,191,5,47,0,0,190,188,1,0,0,0,191,194,1,0,0,0,192,
        190,1,0,0,0,192,193,1,0,0,0,193,31,1,0,0,0,194,192,1,0,0,0,195,196,
        5,23,0,0,196,197,5,24,0,0,197,33,1,0,0,0,198,199,5,27,0,0,199,200,
        5,16,0,0,200,201,5,28,0,0,201,203,5,16,0,0,202,204,3,36,18,0,203,
        202,1,0,0,0,204,205,1,0,0,0,205,203,1,0,0,0,205,206,1,0,0,0,206,
        207,1,0,0,0,207,208,5,17,0,0,208,209,5,29,0,0,209,211,5,16,0,0,210,
        212,3,46,23,0,211,210,1,0,0,0,212,213,1,0,0,0,213,211,1,0,0,0,213,
        214,1,0,0,0,214,215,1,0,0,0,215,216,5,17,0,0,216,217,5,30,0,0,217,
        219,5,16,0,0,218,220,3,48,24,0,219,218,1,0,0,0,220,221,1,0,0,0,221,
        219,1,0,0,0,221,222,1,0,0,0,222,223,1,0,0,0,223,224,5,17,0,0,224,
        225,5,17,0,0,225,35,1,0,0,0,226,227,3,38,19,0,227,228,5,21,0,0,228,
        229,3,42,21,0,229,230,5,33,0,0,230,231,3,44,22,0,231,232,5,19,0,
        0,232,37,1,0,0,0,233,239,3,30,15,0,234,235,5,1,0,0,235,236,3,40,
        20,0,236,237,5,2,0,0,237,239,1,0,0,0,238,233,1,0,0,0,238,234,1,0,
        0,0,239,39,1,0,0,0,240,241,3,30,15,0,241,242,5,21,0,0,242,243,5,
        47,0,0,243,244,5,15,0,0,244,245,3,30,15,0,245,246,5,21,0,0,246,247,
        5,47,0,0,247,41,1,0,0,0,248,249,7,1,0,0,249,43,1,0,0,0,250,251,3,
        50,25,0,251,252,5,3,0,0,252,253,3,50,25,0,253,45,1,0,0,0,254,255,
        7,2,0,0,255,256,5,47,0,0,256,257,5,19,0,0,257,47,1,0,0,0,258,259,
        5,34,0,0,259,260,3,52,26,0,260,261,5,19,0,0,261,49,1,0,0,0,262,263,
        5,23,0,0,263,264,5,24,0,0,264,51,1,0,0,0,265,266,6,26,-1,0,266,267,
        3,54,27,0,267,282,1,0,0,0,268,269,10,4,0,0,269,270,7,3,0,0,270,281,
        3,52,26,5,271,272,10,3,0,0,272,273,7,4,0,0,273,281,3,52,26,4,274,
        275,10,2,0,0,275,276,7,5,0,0,276,281,3,52,26,3,277,278,10,1,0,0,
        278,279,7,6,0,0,279,281,3,52,26,2,280,268,1,0,0,0,280,271,1,0,0,
        0,280,274,1,0,0,0,280,277,1,0,0,0,281,284,1,0,0,0,282,280,1,0,0,
        0,282,283,1,0,0,0,283,53,1,0,0,0,284,282,1,0,0,0,285,293,5,23,0,
        0,286,293,3,50,25,0,287,293,5,47,0,0,288,289,5,1,0,0,289,290,3,52,
        26,0,290,291,5,2,0,0,291,293,1,0,0,0,292,285,1,0,0,0,292,286,1,0,
        0,0,292,287,1,0,0,0,292,288,1,0,0,0,293,55,1,0,0,0,20,59,71,84,99,
        104,110,134,138,146,156,172,185,192,205,213,221,238,280,282,292
    ]

class RoboticsParser ( Parser ):

    grammarFileName = "Robotics.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'('", "')'", "'..'", "'COMPONENT'", "'CONNECT'", 
                     "'PROPERTY'", "'period'", "'deadline'", "'WCET'", "'priority'", 
                     "'latency_budget'", "'SYSTEM'", "'VEHICLE'", "'CPU'", 
                     "'->'", "'{'", "'}'", "':'", "';'", "'='", "'.'", "<INVALID>", 
                     "<INVALID>", "'ms'", "<INVALID>", "<INVALID>", "'OPTIMISATION'", 
                     "'VARIABLES'", "'OBJECTIVES'", "'CONSTRAINTS'", "<INVALID>", 
                     "<INVALID>", "'range'", "'assert'", "'&&'", "'||'", 
                     "'=='", "'!='", "'<='", "'>='", "'<'", "'>'", "'+'", 
                     "'-'", "'*'", "'/'" ]

    symbolicNames = [ "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "COMPONENT", "CONNECT", "PROPERTY", "PERIOD", "DEADLINE", 
                      "WCET", "PRIORITY", "LATENCY_BUDGET", "SYSTEM", "VEHICLE", 
                      "CPU", "ARROW", "LBRACE", "RBRACE", "COLON", "SEMI", 
                      "EQUAL", "DOT", "STRING", "INT", "UNIT_MS", "WS", 
                      "LINE_COMMENT", "OPTIMISATION", "VARIABLES", "OBJECTIVES", 
                      "CONSTRAINTS", "MINIMISE", "MAXIMISE", "RANGE", "ASSERT", 
                      "AND", "OR", "EQ", "NEQ", "LE", "GE", "LT", "GT", 
                      "PLUS", "MINUS", "STAR", "SLASH", "ID" ]

    RULE_file = 0
    RULE_statement = 1
    RULE_componentDecl = 2
    RULE_componentBody = 3
    RULE_componentAttr = 4
    RULE_connectDecl = 5
    RULE_connectBody = 6
    RULE_endpoint = 7
    RULE_propertyDecl = 8
    RULE_vehicleDecl = 9
    RULE_cpuDecl = 10
    RULE_cpuAttr = 11
    RULE_systemDecl = 12
    RULE_propertyField = 13
    RULE_propertyValue = 14
    RULE_dottedId = 15
    RULE_duration = 16
    RULE_optimisationBlock = 17
    RULE_variableDecl = 18
    RULE_targetRef = 19
    RULE_connectionRef = 20
    RULE_attrName = 21
    RULE_rangeSpec = 22
    RULE_objectiveDecl = 23
    RULE_constraintDecl = 24
    RULE_literalDuration = 25
    RULE_expression = 26
    RULE_primary = 27

    ruleNames =  [ "file", "statement", "componentDecl", "componentBody", 
                   "componentAttr", "connectDecl", "connectBody", "endpoint", 
                   "propertyDecl", "vehicleDecl", "cpuDecl", "cpuAttr", 
                   "systemDecl", "propertyField", "propertyValue", "dottedId", 
                   "duration", "optimisationBlock", "variableDecl", "targetRef", 
                   "connectionRef", "attrName", "rangeSpec", "objectiveDecl", 
                   "constraintDecl", "literalDuration", "expression", "primary" ]

    EOF = Token.EOF
    T__0=1
    T__1=2
    T__2=3
    COMPONENT=4
    CONNECT=5
    PROPERTY=6
    PERIOD=7
    DEADLINE=8
    WCET=9
    PRIORITY=10
    LATENCY_BUDGET=11
    SYSTEM=12
    VEHICLE=13
    CPU=14
    ARROW=15
    LBRACE=16
    RBRACE=17
    COLON=18
    SEMI=19
    EQUAL=20
    DOT=21
    STRING=22
    INT=23
    UNIT_MS=24
    WS=25
    LINE_COMMENT=26
    OPTIMISATION=27
    VARIABLES=28
    OBJECTIVES=29
    CONSTRAINTS=30
    MINIMISE=31
    MAXIMISE=32
    RANGE=33
    ASSERT=34
    AND=35
    OR=36
    EQ=37
    NEQ=38
    LE=39
    GE=40
    LT=41
    GT=42
    PLUS=43
    MINUS=44
    STAR=45
    SLASH=46
    ID=47

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.13.2")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class FileContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def EOF(self):
            return self.getToken(RoboticsParser.EOF, 0)

        def statement(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(RoboticsParser.StatementContext)
            else:
                return self.getTypedRuleContext(RoboticsParser.StatementContext,i)


        def getRuleIndex(self):
            return RoboticsParser.RULE_file

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterFile" ):
                listener.enterFile(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitFile" ):
                listener.exitFile(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitFile" ):
                return visitor.visitFile(self)
            else:
                return visitor.visitChildren(self)




    def file_(self):

        localctx = RoboticsParser.FileContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_file)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 59
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & 134246512) != 0):
                self.state = 56
                self.statement()
                self.state = 61
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 62
            self.match(RoboticsParser.EOF)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class StatementContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def componentDecl(self):
            return self.getTypedRuleContext(RoboticsParser.ComponentDeclContext,0)


        def connectDecl(self):
            return self.getTypedRuleContext(RoboticsParser.ConnectDeclContext,0)


        def propertyDecl(self):
            return self.getTypedRuleContext(RoboticsParser.PropertyDeclContext,0)


        def optimisationBlock(self):
            return self.getTypedRuleContext(RoboticsParser.OptimisationBlockContext,0)


        def systemDecl(self):
            return self.getTypedRuleContext(RoboticsParser.SystemDeclContext,0)


        def vehicleDecl(self):
            return self.getTypedRuleContext(RoboticsParser.VehicleDeclContext,0)


        def cpuDecl(self):
            return self.getTypedRuleContext(RoboticsParser.CpuDeclContext,0)


        def getRuleIndex(self):
            return RoboticsParser.RULE_statement

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterStatement" ):
                listener.enterStatement(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitStatement" ):
                listener.exitStatement(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitStatement" ):
                return visitor.visitStatement(self)
            else:
                return visitor.visitChildren(self)




    def statement(self):

        localctx = RoboticsParser.StatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_statement)
        try:
            self.state = 71
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [4]:
                self.enterOuterAlt(localctx, 1)
                self.state = 64
                self.componentDecl()
                pass
            elif token in [5]:
                self.enterOuterAlt(localctx, 2)
                self.state = 65
                self.connectDecl()
                pass
            elif token in [6]:
                self.enterOuterAlt(localctx, 3)
                self.state = 66
                self.propertyDecl()
                pass
            elif token in [27]:
                self.enterOuterAlt(localctx, 4)
                self.state = 67
                self.optimisationBlock()
                pass
            elif token in [12]:
                self.enterOuterAlt(localctx, 5)
                self.state = 68
                self.systemDecl()
                pass
            elif token in [13]:
                self.enterOuterAlt(localctx, 6)
                self.state = 69
                self.vehicleDecl()
                pass
            elif token in [14]:
                self.enterOuterAlt(localctx, 7)
                self.state = 70
                self.cpuDecl()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ComponentDeclContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def COMPONENT(self):
            return self.getToken(RoboticsParser.COMPONENT, 0)

        def ID(self):
            return self.getToken(RoboticsParser.ID, 0)

        def LBRACE(self):
            return self.getToken(RoboticsParser.LBRACE, 0)

        def componentBody(self):
            return self.getTypedRuleContext(RoboticsParser.ComponentBodyContext,0)


        def RBRACE(self):
            return self.getToken(RoboticsParser.RBRACE, 0)

        def getRuleIndex(self):
            return RoboticsParser.RULE_componentDecl

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterComponentDecl" ):
                listener.enterComponentDecl(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitComponentDecl" ):
                listener.exitComponentDecl(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitComponentDecl" ):
                return visitor.visitComponentDecl(self)
            else:
                return visitor.visitChildren(self)




    def componentDecl(self):

        localctx = RoboticsParser.ComponentDeclContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_componentDecl)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 73
            self.match(RoboticsParser.COMPONENT)
            self.state = 74
            self.match(RoboticsParser.ID)
            self.state = 75
            self.match(RoboticsParser.LBRACE)
            self.state = 76
            self.componentBody()
            self.state = 77
            self.match(RoboticsParser.RBRACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ComponentBodyContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def componentAttr(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(RoboticsParser.ComponentAttrContext)
            else:
                return self.getTypedRuleContext(RoboticsParser.ComponentAttrContext,i)


        def SEMI(self, i:int=None):
            if i is None:
                return self.getTokens(RoboticsParser.SEMI)
            else:
                return self.getToken(RoboticsParser.SEMI, i)

        def getRuleIndex(self):
            return RoboticsParser.RULE_componentBody

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterComponentBody" ):
                listener.enterComponentBody(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitComponentBody" ):
                listener.exitComponentBody(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitComponentBody" ):
                return visitor.visitComponentBody(self)
            else:
                return visitor.visitChildren(self)




    def componentBody(self):

        localctx = RoboticsParser.ComponentBodyContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_componentBody)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 84
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & 1920) != 0):
                self.state = 79
                self.componentAttr()
                self.state = 80
                self.match(RoboticsParser.SEMI)
                self.state = 86
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ComponentAttrContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def PERIOD(self):
            return self.getToken(RoboticsParser.PERIOD, 0)

        def EQUAL(self):
            return self.getToken(RoboticsParser.EQUAL, 0)

        def duration(self):
            return self.getTypedRuleContext(RoboticsParser.DurationContext,0)


        def DEADLINE(self):
            return self.getToken(RoboticsParser.DEADLINE, 0)

        def WCET(self):
            return self.getToken(RoboticsParser.WCET, 0)

        def PRIORITY(self):
            return self.getToken(RoboticsParser.PRIORITY, 0)

        def INT(self):
            return self.getToken(RoboticsParser.INT, 0)

        def getRuleIndex(self):
            return RoboticsParser.RULE_componentAttr

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterComponentAttr" ):
                listener.enterComponentAttr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitComponentAttr" ):
                listener.exitComponentAttr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitComponentAttr" ):
                return visitor.visitComponentAttr(self)
            else:
                return visitor.visitChildren(self)




    def componentAttr(self):

        localctx = RoboticsParser.ComponentAttrContext(self, self._ctx, self.state)
        self.enterRule(localctx, 8, self.RULE_componentAttr)
        try:
            self.state = 99
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [7]:
                self.enterOuterAlt(localctx, 1)
                self.state = 87
                self.match(RoboticsParser.PERIOD)
                self.state = 88
                self.match(RoboticsParser.EQUAL)
                self.state = 89
                self.duration()
                pass
            elif token in [8]:
                self.enterOuterAlt(localctx, 2)
                self.state = 90
                self.match(RoboticsParser.DEADLINE)
                self.state = 91
                self.match(RoboticsParser.EQUAL)
                self.state = 92
                self.duration()
                pass
            elif token in [9]:
                self.enterOuterAlt(localctx, 3)
                self.state = 93
                self.match(RoboticsParser.WCET)
                self.state = 94
                self.match(RoboticsParser.EQUAL)
                self.state = 95
                self.duration()
                pass
            elif token in [10]:
                self.enterOuterAlt(localctx, 4)
                self.state = 96
                self.match(RoboticsParser.PRIORITY)
                self.state = 97
                self.match(RoboticsParser.EQUAL)
                self.state = 98
                self.match(RoboticsParser.INT)
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ConnectDeclContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.src = None # EndpointContext
            self.dst = None # EndpointContext

        def CONNECT(self):
            return self.getToken(RoboticsParser.CONNECT, 0)

        def ARROW(self):
            return self.getToken(RoboticsParser.ARROW, 0)

        def endpoint(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(RoboticsParser.EndpointContext)
            else:
                return self.getTypedRuleContext(RoboticsParser.EndpointContext,i)


        def ID(self):
            return self.getToken(RoboticsParser.ID, 0)

        def COLON(self):
            return self.getToken(RoboticsParser.COLON, 0)

        def connectBody(self):
            return self.getTypedRuleContext(RoboticsParser.ConnectBodyContext,0)


        def getRuleIndex(self):
            return RoboticsParser.RULE_connectDecl

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterConnectDecl" ):
                listener.enterConnectDecl(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitConnectDecl" ):
                listener.exitConnectDecl(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitConnectDecl" ):
                return visitor.visitConnectDecl(self)
            else:
                return visitor.visitChildren(self)




    def connectDecl(self):

        localctx = RoboticsParser.ConnectDeclContext(self, self._ctx, self.state)
        self.enterRule(localctx, 10, self.RULE_connectDecl)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 101
            self.match(RoboticsParser.CONNECT)
            self.state = 104
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,4,self._ctx)
            if la_ == 1:
                self.state = 102
                self.match(RoboticsParser.ID)
                self.state = 103
                self.match(RoboticsParser.COLON)


            self.state = 106
            localctx.src = self.endpoint()
            self.state = 107
            self.match(RoboticsParser.ARROW)
            self.state = 108
            localctx.dst = self.endpoint()
            self.state = 110
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==16:
                self.state = 109
                self.connectBody()


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ConnectBodyContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def LBRACE(self):
            return self.getToken(RoboticsParser.LBRACE, 0)

        def LATENCY_BUDGET(self):
            return self.getToken(RoboticsParser.LATENCY_BUDGET, 0)

        def EQUAL(self):
            return self.getToken(RoboticsParser.EQUAL, 0)

        def duration(self):
            return self.getTypedRuleContext(RoboticsParser.DurationContext,0)


        def SEMI(self):
            return self.getToken(RoboticsParser.SEMI, 0)

        def RBRACE(self):
            return self.getToken(RoboticsParser.RBRACE, 0)

        def getRuleIndex(self):
            return RoboticsParser.RULE_connectBody

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterConnectBody" ):
                listener.enterConnectBody(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitConnectBody" ):
                listener.exitConnectBody(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitConnectBody" ):
                return visitor.visitConnectBody(self)
            else:
                return visitor.visitChildren(self)




    def connectBody(self):

        localctx = RoboticsParser.ConnectBodyContext(self, self._ctx, self.state)
        self.enterRule(localctx, 12, self.RULE_connectBody)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 112
            self.match(RoboticsParser.LBRACE)
            self.state = 113
            self.match(RoboticsParser.LATENCY_BUDGET)
            self.state = 114
            self.match(RoboticsParser.EQUAL)
            self.state = 115
            self.duration()
            self.state = 116
            self.match(RoboticsParser.SEMI)
            self.state = 117
            self.match(RoboticsParser.RBRACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class EndpointContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.comp = None # DottedIdContext
            self.port = None # Token

        def DOT(self):
            return self.getToken(RoboticsParser.DOT, 0)

        def dottedId(self):
            return self.getTypedRuleContext(RoboticsParser.DottedIdContext,0)


        def ID(self):
            return self.getToken(RoboticsParser.ID, 0)

        def getRuleIndex(self):
            return RoboticsParser.RULE_endpoint

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterEndpoint" ):
                listener.enterEndpoint(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitEndpoint" ):
                listener.exitEndpoint(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitEndpoint" ):
                return visitor.visitEndpoint(self)
            else:
                return visitor.visitChildren(self)




    def endpoint(self):

        localctx = RoboticsParser.EndpointContext(self, self._ctx, self.state)
        self.enterRule(localctx, 14, self.RULE_endpoint)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 119
            localctx.comp = self.dottedId()
            self.state = 120
            self.match(RoboticsParser.DOT)
            self.state = 121
            localctx.port = self.match(RoboticsParser.ID)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class PropertyDeclContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return RoboticsParser.RULE_propertyDecl

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class PropertyBlockContext(PropertyDeclContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a RoboticsParser.PropertyDeclContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def PROPERTY(self):
            return self.getToken(RoboticsParser.PROPERTY, 0)
        def ID(self):
            return self.getToken(RoboticsParser.ID, 0)
        def LBRACE(self):
            return self.getToken(RoboticsParser.LBRACE, 0)
        def RBRACE(self):
            return self.getToken(RoboticsParser.RBRACE, 0)
        def propertyField(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(RoboticsParser.PropertyFieldContext)
            else:
                return self.getTypedRuleContext(RoboticsParser.PropertyFieldContext,i)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterPropertyBlock" ):
                listener.enterPropertyBlock(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitPropertyBlock" ):
                listener.exitPropertyBlock(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPropertyBlock" ):
                return visitor.visitPropertyBlock(self)
            else:
                return visitor.visitChildren(self)


    class PropertyStringContext(PropertyDeclContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a RoboticsParser.PropertyDeclContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def PROPERTY(self):
            return self.getToken(RoboticsParser.PROPERTY, 0)
        def ID(self):
            return self.getToken(RoboticsParser.ID, 0)
        def COLON(self):
            return self.getToken(RoboticsParser.COLON, 0)
        def STRING(self):
            return self.getToken(RoboticsParser.STRING, 0)
        def SEMI(self):
            return self.getToken(RoboticsParser.SEMI, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterPropertyString" ):
                listener.enterPropertyString(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitPropertyString" ):
                listener.exitPropertyString(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPropertyString" ):
                return visitor.visitPropertyString(self)
            else:
                return visitor.visitChildren(self)



    def propertyDecl(self):

        localctx = RoboticsParser.PropertyDeclContext(self, self._ctx, self.state)
        self.enterRule(localctx, 16, self.RULE_propertyDecl)
        self._la = 0 # Token type
        try:
            self.state = 138
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,7,self._ctx)
            if la_ == 1:
                localctx = RoboticsParser.PropertyStringContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 123
                self.match(RoboticsParser.PROPERTY)
                self.state = 124
                self.match(RoboticsParser.ID)
                self.state = 125
                self.match(RoboticsParser.COLON)
                self.state = 126
                self.match(RoboticsParser.STRING)
                self.state = 127
                self.match(RoboticsParser.SEMI)
                pass

            elif la_ == 2:
                localctx = RoboticsParser.PropertyBlockContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 128
                self.match(RoboticsParser.PROPERTY)
                self.state = 129
                self.match(RoboticsParser.ID)
                self.state = 130
                self.match(RoboticsParser.LBRACE)
                self.state = 134
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                while _la==47:
                    self.state = 131
                    self.propertyField()
                    self.state = 136
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)

                self.state = 137
                self.match(RoboticsParser.RBRACE)
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class VehicleDeclContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def VEHICLE(self):
            return self.getToken(RoboticsParser.VEHICLE, 0)

        def ID(self):
            return self.getToken(RoboticsParser.ID, 0)

        def LBRACE(self):
            return self.getToken(RoboticsParser.LBRACE, 0)

        def RBRACE(self):
            return self.getToken(RoboticsParser.RBRACE, 0)

        def componentDecl(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(RoboticsParser.ComponentDeclContext)
            else:
                return self.getTypedRuleContext(RoboticsParser.ComponentDeclContext,i)


        def getRuleIndex(self):
            return RoboticsParser.RULE_vehicleDecl

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterVehicleDecl" ):
                listener.enterVehicleDecl(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitVehicleDecl" ):
                listener.exitVehicleDecl(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitVehicleDecl" ):
                return visitor.visitVehicleDecl(self)
            else:
                return visitor.visitChildren(self)




    def vehicleDecl(self):

        localctx = RoboticsParser.VehicleDeclContext(self, self._ctx, self.state)
        self.enterRule(localctx, 18, self.RULE_vehicleDecl)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 140
            self.match(RoboticsParser.VEHICLE)
            self.state = 141
            self.match(RoboticsParser.ID)
            self.state = 142
            self.match(RoboticsParser.LBRACE)
            self.state = 146
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==4:
                self.state = 143
                self.componentDecl()
                self.state = 148
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 149
            self.match(RoboticsParser.RBRACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class CpuDeclContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def CPU(self):
            return self.getToken(RoboticsParser.CPU, 0)

        def LBRACE(self):
            return self.getToken(RoboticsParser.LBRACE, 0)

        def RBRACE(self):
            return self.getToken(RoboticsParser.RBRACE, 0)

        def cpuAttr(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(RoboticsParser.CpuAttrContext)
            else:
                return self.getTypedRuleContext(RoboticsParser.CpuAttrContext,i)


        def getRuleIndex(self):
            return RoboticsParser.RULE_cpuDecl

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterCpuDecl" ):
                listener.enterCpuDecl(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitCpuDecl" ):
                listener.exitCpuDecl(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitCpuDecl" ):
                return visitor.visitCpuDecl(self)
            else:
                return visitor.visitChildren(self)




    def cpuDecl(self):

        localctx = RoboticsParser.CpuDeclContext(self, self._ctx, self.state)
        self.enterRule(localctx, 20, self.RULE_cpuDecl)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 151
            self.match(RoboticsParser.CPU)
            self.state = 152
            self.match(RoboticsParser.LBRACE)
            self.state = 156
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==47:
                self.state = 153
                self.cpuAttr()
                self.state = 158
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 159
            self.match(RoboticsParser.RBRACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class CpuAttrContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ID(self, i:int=None):
            if i is None:
                return self.getTokens(RoboticsParser.ID)
            else:
                return self.getToken(RoboticsParser.ID, i)

        def EQUAL(self):
            return self.getToken(RoboticsParser.EQUAL, 0)

        def SEMI(self):
            return self.getToken(RoboticsParser.SEMI, 0)

        def INT(self):
            return self.getToken(RoboticsParser.INT, 0)

        def getRuleIndex(self):
            return RoboticsParser.RULE_cpuAttr

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterCpuAttr" ):
                listener.enterCpuAttr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitCpuAttr" ):
                listener.exitCpuAttr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitCpuAttr" ):
                return visitor.visitCpuAttr(self)
            else:
                return visitor.visitChildren(self)




    def cpuAttr(self):

        localctx = RoboticsParser.CpuAttrContext(self, self._ctx, self.state)
        self.enterRule(localctx, 22, self.RULE_cpuAttr)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 161
            self.match(RoboticsParser.ID)
            self.state = 162
            self.match(RoboticsParser.EQUAL)
            self.state = 163
            _la = self._input.LA(1)
            if not(_la==23 or _la==47):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
            self.state = 164
            self.match(RoboticsParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class SystemDeclContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def SYSTEM(self):
            return self.getToken(RoboticsParser.SYSTEM, 0)

        def ID(self):
            return self.getToken(RoboticsParser.ID, 0)

        def LBRACE(self):
            return self.getToken(RoboticsParser.LBRACE, 0)

        def RBRACE(self):
            return self.getToken(RoboticsParser.RBRACE, 0)

        def statement(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(RoboticsParser.StatementContext)
            else:
                return self.getTypedRuleContext(RoboticsParser.StatementContext,i)


        def getRuleIndex(self):
            return RoboticsParser.RULE_systemDecl

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterSystemDecl" ):
                listener.enterSystemDecl(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitSystemDecl" ):
                listener.exitSystemDecl(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitSystemDecl" ):
                return visitor.visitSystemDecl(self)
            else:
                return visitor.visitChildren(self)




    def systemDecl(self):

        localctx = RoboticsParser.SystemDeclContext(self, self._ctx, self.state)
        self.enterRule(localctx, 24, self.RULE_systemDecl)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 166
            self.match(RoboticsParser.SYSTEM)
            self.state = 167
            self.match(RoboticsParser.ID)
            self.state = 168
            self.match(RoboticsParser.LBRACE)
            self.state = 172
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & 134246512) != 0):
                self.state = 169
                self.statement()
                self.state = 174
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 175
            self.match(RoboticsParser.RBRACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class PropertyFieldContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ID(self):
            return self.getToken(RoboticsParser.ID, 0)

        def EQUAL(self):
            return self.getToken(RoboticsParser.EQUAL, 0)

        def propertyValue(self):
            return self.getTypedRuleContext(RoboticsParser.PropertyValueContext,0)


        def SEMI(self):
            return self.getToken(RoboticsParser.SEMI, 0)

        def getRuleIndex(self):
            return RoboticsParser.RULE_propertyField

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterPropertyField" ):
                listener.enterPropertyField(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitPropertyField" ):
                listener.exitPropertyField(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPropertyField" ):
                return visitor.visitPropertyField(self)
            else:
                return visitor.visitChildren(self)




    def propertyField(self):

        localctx = RoboticsParser.PropertyFieldContext(self, self._ctx, self.state)
        self.enterRule(localctx, 26, self.RULE_propertyField)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 177
            self.match(RoboticsParser.ID)
            self.state = 178
            self.match(RoboticsParser.EQUAL)
            self.state = 179
            self.propertyValue()
            self.state = 180
            self.match(RoboticsParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class PropertyValueContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def duration(self):
            return self.getTypedRuleContext(RoboticsParser.DurationContext,0)


        def dottedId(self):
            return self.getTypedRuleContext(RoboticsParser.DottedIdContext,0)


        def ID(self):
            return self.getToken(RoboticsParser.ID, 0)

        def getRuleIndex(self):
            return RoboticsParser.RULE_propertyValue

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterPropertyValue" ):
                listener.enterPropertyValue(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitPropertyValue" ):
                listener.exitPropertyValue(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPropertyValue" ):
                return visitor.visitPropertyValue(self)
            else:
                return visitor.visitChildren(self)




    def propertyValue(self):

        localctx = RoboticsParser.PropertyValueContext(self, self._ctx, self.state)
        self.enterRule(localctx, 28, self.RULE_propertyValue)
        try:
            self.state = 185
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,11,self._ctx)
            if la_ == 1:
                self.enterOuterAlt(localctx, 1)
                self.state = 182
                self.duration()
                pass

            elif la_ == 2:
                self.enterOuterAlt(localctx, 2)
                self.state = 183
                self.dottedId()
                pass

            elif la_ == 3:
                self.enterOuterAlt(localctx, 3)
                self.state = 184
                self.match(RoboticsParser.ID)
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class DottedIdContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ID(self, i:int=None):
            if i is None:
                return self.getTokens(RoboticsParser.ID)
            else:
                return self.getToken(RoboticsParser.ID, i)

        def DOT(self, i:int=None):
            if i is None:
                return self.getTokens(RoboticsParser.DOT)
            else:
                return self.getToken(RoboticsParser.DOT, i)

        def getRuleIndex(self):
            return RoboticsParser.RULE_dottedId

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDottedId" ):
                listener.enterDottedId(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDottedId" ):
                listener.exitDottedId(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitDottedId" ):
                return visitor.visitDottedId(self)
            else:
                return visitor.visitChildren(self)




    def dottedId(self):

        localctx = RoboticsParser.DottedIdContext(self, self._ctx, self.state)
        self.enterRule(localctx, 30, self.RULE_dottedId)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 187
            self.match(RoboticsParser.ID)
            self.state = 192
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,12,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 188
                    self.match(RoboticsParser.DOT)
                    self.state = 189
                    self.match(RoboticsParser.ID) 
                self.state = 194
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,12,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class DurationContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def INT(self):
            return self.getToken(RoboticsParser.INT, 0)

        def UNIT_MS(self):
            return self.getToken(RoboticsParser.UNIT_MS, 0)

        def getRuleIndex(self):
            return RoboticsParser.RULE_duration

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDuration" ):
                listener.enterDuration(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDuration" ):
                listener.exitDuration(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitDuration" ):
                return visitor.visitDuration(self)
            else:
                return visitor.visitChildren(self)




    def duration(self):

        localctx = RoboticsParser.DurationContext(self, self._ctx, self.state)
        self.enterRule(localctx, 32, self.RULE_duration)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 195
            self.match(RoboticsParser.INT)
            self.state = 196
            self.match(RoboticsParser.UNIT_MS)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class OptimisationBlockContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def OPTIMISATION(self):
            return self.getToken(RoboticsParser.OPTIMISATION, 0)

        def LBRACE(self, i:int=None):
            if i is None:
                return self.getTokens(RoboticsParser.LBRACE)
            else:
                return self.getToken(RoboticsParser.LBRACE, i)

        def VARIABLES(self):
            return self.getToken(RoboticsParser.VARIABLES, 0)

        def RBRACE(self, i:int=None):
            if i is None:
                return self.getTokens(RoboticsParser.RBRACE)
            else:
                return self.getToken(RoboticsParser.RBRACE, i)

        def OBJECTIVES(self):
            return self.getToken(RoboticsParser.OBJECTIVES, 0)

        def CONSTRAINTS(self):
            return self.getToken(RoboticsParser.CONSTRAINTS, 0)

        def variableDecl(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(RoboticsParser.VariableDeclContext)
            else:
                return self.getTypedRuleContext(RoboticsParser.VariableDeclContext,i)


        def objectiveDecl(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(RoboticsParser.ObjectiveDeclContext)
            else:
                return self.getTypedRuleContext(RoboticsParser.ObjectiveDeclContext,i)


        def constraintDecl(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(RoboticsParser.ConstraintDeclContext)
            else:
                return self.getTypedRuleContext(RoboticsParser.ConstraintDeclContext,i)


        def getRuleIndex(self):
            return RoboticsParser.RULE_optimisationBlock

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterOptimisationBlock" ):
                listener.enterOptimisationBlock(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitOptimisationBlock" ):
                listener.exitOptimisationBlock(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitOptimisationBlock" ):
                return visitor.visitOptimisationBlock(self)
            else:
                return visitor.visitChildren(self)




    def optimisationBlock(self):

        localctx = RoboticsParser.OptimisationBlockContext(self, self._ctx, self.state)
        self.enterRule(localctx, 34, self.RULE_optimisationBlock)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 198
            self.match(RoboticsParser.OPTIMISATION)
            self.state = 199
            self.match(RoboticsParser.LBRACE)
            self.state = 200
            self.match(RoboticsParser.VARIABLES)
            self.state = 201
            self.match(RoboticsParser.LBRACE)
            self.state = 203 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 202
                self.variableDecl()
                self.state = 205 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (_la==1 or _la==47):
                    break

            self.state = 207
            self.match(RoboticsParser.RBRACE)
            self.state = 208
            self.match(RoboticsParser.OBJECTIVES)
            self.state = 209
            self.match(RoboticsParser.LBRACE)
            self.state = 211 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 210
                self.objectiveDecl()
                self.state = 213 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (_la==31 or _la==32):
                    break

            self.state = 215
            self.match(RoboticsParser.RBRACE)
            self.state = 216
            self.match(RoboticsParser.CONSTRAINTS)
            self.state = 217
            self.match(RoboticsParser.LBRACE)
            self.state = 219 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 218
                self.constraintDecl()
                self.state = 221 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (_la==34):
                    break

            self.state = 223
            self.match(RoboticsParser.RBRACE)
            self.state = 224
            self.match(RoboticsParser.RBRACE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class VariableDeclContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def targetRef(self):
            return self.getTypedRuleContext(RoboticsParser.TargetRefContext,0)


        def DOT(self):
            return self.getToken(RoboticsParser.DOT, 0)

        def attrName(self):
            return self.getTypedRuleContext(RoboticsParser.AttrNameContext,0)


        def RANGE(self):
            return self.getToken(RoboticsParser.RANGE, 0)

        def rangeSpec(self):
            return self.getTypedRuleContext(RoboticsParser.RangeSpecContext,0)


        def SEMI(self):
            return self.getToken(RoboticsParser.SEMI, 0)

        def getRuleIndex(self):
            return RoboticsParser.RULE_variableDecl

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterVariableDecl" ):
                listener.enterVariableDecl(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitVariableDecl" ):
                listener.exitVariableDecl(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitVariableDecl" ):
                return visitor.visitVariableDecl(self)
            else:
                return visitor.visitChildren(self)




    def variableDecl(self):

        localctx = RoboticsParser.VariableDeclContext(self, self._ctx, self.state)
        self.enterRule(localctx, 36, self.RULE_variableDecl)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 226
            self.targetRef()
            self.state = 227
            self.match(RoboticsParser.DOT)
            self.state = 228
            self.attrName()
            self.state = 229
            self.match(RoboticsParser.RANGE)
            self.state = 230
            self.rangeSpec()
            self.state = 231
            self.match(RoboticsParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class TargetRefContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return RoboticsParser.RULE_targetRef

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class ConnectionRefWrappedContext(TargetRefContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a RoboticsParser.TargetRefContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def connectionRef(self):
            return self.getTypedRuleContext(RoboticsParser.ConnectionRefContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterConnectionRefWrapped" ):
                listener.enterConnectionRefWrapped(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitConnectionRefWrapped" ):
                listener.exitConnectionRefWrapped(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitConnectionRefWrapped" ):
                return visitor.visitConnectionRefWrapped(self)
            else:
                return visitor.visitChildren(self)


    class ComponentRefContext(TargetRefContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a RoboticsParser.TargetRefContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def dottedId(self):
            return self.getTypedRuleContext(RoboticsParser.DottedIdContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterComponentRef" ):
                listener.enterComponentRef(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitComponentRef" ):
                listener.exitComponentRef(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitComponentRef" ):
                return visitor.visitComponentRef(self)
            else:
                return visitor.visitChildren(self)



    def targetRef(self):

        localctx = RoboticsParser.TargetRefContext(self, self._ctx, self.state)
        self.enterRule(localctx, 38, self.RULE_targetRef)
        try:
            self.state = 238
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [47]:
                localctx = RoboticsParser.ComponentRefContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 233
                self.dottedId()
                pass
            elif token in [1]:
                localctx = RoboticsParser.ConnectionRefWrappedContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 234
                self.match(RoboticsParser.T__0)
                self.state = 235
                self.connectionRef()
                self.state = 236
                self.match(RoboticsParser.T__1)
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ConnectionRefContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def dottedId(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(RoboticsParser.DottedIdContext)
            else:
                return self.getTypedRuleContext(RoboticsParser.DottedIdContext,i)


        def DOT(self, i:int=None):
            if i is None:
                return self.getTokens(RoboticsParser.DOT)
            else:
                return self.getToken(RoboticsParser.DOT, i)

        def ID(self, i:int=None):
            if i is None:
                return self.getTokens(RoboticsParser.ID)
            else:
                return self.getToken(RoboticsParser.ID, i)

        def ARROW(self):
            return self.getToken(RoboticsParser.ARROW, 0)

        def getRuleIndex(self):
            return RoboticsParser.RULE_connectionRef

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterConnectionRef" ):
                listener.enterConnectionRef(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitConnectionRef" ):
                listener.exitConnectionRef(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitConnectionRef" ):
                return visitor.visitConnectionRef(self)
            else:
                return visitor.visitChildren(self)




    def connectionRef(self):

        localctx = RoboticsParser.ConnectionRefContext(self, self._ctx, self.state)
        self.enterRule(localctx, 40, self.RULE_connectionRef)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 240
            self.dottedId()
            self.state = 241
            self.match(RoboticsParser.DOT)
            self.state = 242
            self.match(RoboticsParser.ID)
            self.state = 243
            self.match(RoboticsParser.ARROW)
            self.state = 244
            self.dottedId()
            self.state = 245
            self.match(RoboticsParser.DOT)
            self.state = 246
            self.match(RoboticsParser.ID)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class AttrNameContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def PERIOD(self):
            return self.getToken(RoboticsParser.PERIOD, 0)

        def DEADLINE(self):
            return self.getToken(RoboticsParser.DEADLINE, 0)

        def WCET(self):
            return self.getToken(RoboticsParser.WCET, 0)

        def PRIORITY(self):
            return self.getToken(RoboticsParser.PRIORITY, 0)

        def LATENCY_BUDGET(self):
            return self.getToken(RoboticsParser.LATENCY_BUDGET, 0)

        def ID(self):
            return self.getToken(RoboticsParser.ID, 0)

        def getRuleIndex(self):
            return RoboticsParser.RULE_attrName

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterAttrName" ):
                listener.enterAttrName(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitAttrName" ):
                listener.exitAttrName(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAttrName" ):
                return visitor.visitAttrName(self)
            else:
                return visitor.visitChildren(self)




    def attrName(self):

        localctx = RoboticsParser.AttrNameContext(self, self._ctx, self.state)
        self.enterRule(localctx, 42, self.RULE_attrName)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 248
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 140737488359296) != 0)):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class RangeSpecContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def literalDuration(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(RoboticsParser.LiteralDurationContext)
            else:
                return self.getTypedRuleContext(RoboticsParser.LiteralDurationContext,i)


        def getRuleIndex(self):
            return RoboticsParser.RULE_rangeSpec

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterRangeSpec" ):
                listener.enterRangeSpec(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitRangeSpec" ):
                listener.exitRangeSpec(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRangeSpec" ):
                return visitor.visitRangeSpec(self)
            else:
                return visitor.visitChildren(self)




    def rangeSpec(self):

        localctx = RoboticsParser.RangeSpecContext(self, self._ctx, self.state)
        self.enterRule(localctx, 44, self.RULE_rangeSpec)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 250
            self.literalDuration()
            self.state = 251
            self.match(RoboticsParser.T__2)
            self.state = 252
            self.literalDuration()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ObjectiveDeclContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ID(self):
            return self.getToken(RoboticsParser.ID, 0)

        def SEMI(self):
            return self.getToken(RoboticsParser.SEMI, 0)

        def MINIMISE(self):
            return self.getToken(RoboticsParser.MINIMISE, 0)

        def MAXIMISE(self):
            return self.getToken(RoboticsParser.MAXIMISE, 0)

        def getRuleIndex(self):
            return RoboticsParser.RULE_objectiveDecl

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterObjectiveDecl" ):
                listener.enterObjectiveDecl(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitObjectiveDecl" ):
                listener.exitObjectiveDecl(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitObjectiveDecl" ):
                return visitor.visitObjectiveDecl(self)
            else:
                return visitor.visitChildren(self)




    def objectiveDecl(self):

        localctx = RoboticsParser.ObjectiveDeclContext(self, self._ctx, self.state)
        self.enterRule(localctx, 46, self.RULE_objectiveDecl)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 254
            _la = self._input.LA(1)
            if not(_la==31 or _la==32):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
            self.state = 255
            self.match(RoboticsParser.ID)
            self.state = 256
            self.match(RoboticsParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ConstraintDeclContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ASSERT(self):
            return self.getToken(RoboticsParser.ASSERT, 0)

        def expression(self):
            return self.getTypedRuleContext(RoboticsParser.ExpressionContext,0)


        def SEMI(self):
            return self.getToken(RoboticsParser.SEMI, 0)

        def getRuleIndex(self):
            return RoboticsParser.RULE_constraintDecl

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterConstraintDecl" ):
                listener.enterConstraintDecl(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitConstraintDecl" ):
                listener.exitConstraintDecl(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitConstraintDecl" ):
                return visitor.visitConstraintDecl(self)
            else:
                return visitor.visitChildren(self)




    def constraintDecl(self):

        localctx = RoboticsParser.ConstraintDeclContext(self, self._ctx, self.state)
        self.enterRule(localctx, 48, self.RULE_constraintDecl)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 258
            self.match(RoboticsParser.ASSERT)
            self.state = 259
            self.expression(0)
            self.state = 260
            self.match(RoboticsParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class LiteralDurationContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def INT(self):
            return self.getToken(RoboticsParser.INT, 0)

        def UNIT_MS(self):
            return self.getToken(RoboticsParser.UNIT_MS, 0)

        def getRuleIndex(self):
            return RoboticsParser.RULE_literalDuration

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterLiteralDuration" ):
                listener.enterLiteralDuration(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitLiteralDuration" ):
                listener.exitLiteralDuration(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitLiteralDuration" ):
                return visitor.visitLiteralDuration(self)
            else:
                return visitor.visitChildren(self)




    def literalDuration(self):

        localctx = RoboticsParser.LiteralDurationContext(self, self._ctx, self.state)
        self.enterRule(localctx, 50, self.RULE_literalDuration)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 262
            self.match(RoboticsParser.INT)
            self.state = 263
            self.match(RoboticsParser.UNIT_MS)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ExpressionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return RoboticsParser.RULE_expression

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)


    class AddSubExprContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a RoboticsParser.ExpressionContext
            super().__init__(parser)
            self.left = None # ExpressionContext
            self.op = None # Token
            self.right = None # ExpressionContext
            self.copyFrom(ctx)

        def expression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(RoboticsParser.ExpressionContext)
            else:
                return self.getTypedRuleContext(RoboticsParser.ExpressionContext,i)

        def PLUS(self):
            return self.getToken(RoboticsParser.PLUS, 0)
        def MINUS(self):
            return self.getToken(RoboticsParser.MINUS, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterAddSubExpr" ):
                listener.enterAddSubExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitAddSubExpr" ):
                listener.exitAddSubExpr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAddSubExpr" ):
                return visitor.visitAddSubExpr(self)
            else:
                return visitor.visitChildren(self)


    class CompExprContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a RoboticsParser.ExpressionContext
            super().__init__(parser)
            self.left = None # ExpressionContext
            self.op = None # Token
            self.right = None # ExpressionContext
            self.copyFrom(ctx)

        def expression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(RoboticsParser.ExpressionContext)
            else:
                return self.getTypedRuleContext(RoboticsParser.ExpressionContext,i)

        def LT(self):
            return self.getToken(RoboticsParser.LT, 0)
        def LE(self):
            return self.getToken(RoboticsParser.LE, 0)
        def GT(self):
            return self.getToken(RoboticsParser.GT, 0)
        def GE(self):
            return self.getToken(RoboticsParser.GE, 0)
        def EQ(self):
            return self.getToken(RoboticsParser.EQ, 0)
        def NEQ(self):
            return self.getToken(RoboticsParser.NEQ, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterCompExpr" ):
                listener.enterCompExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitCompExpr" ):
                listener.exitCompExpr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitCompExpr" ):
                return visitor.visitCompExpr(self)
            else:
                return visitor.visitChildren(self)


    class LogicExprContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a RoboticsParser.ExpressionContext
            super().__init__(parser)
            self.left = None # ExpressionContext
            self.op = None # Token
            self.right = None # ExpressionContext
            self.copyFrom(ctx)

        def expression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(RoboticsParser.ExpressionContext)
            else:
                return self.getTypedRuleContext(RoboticsParser.ExpressionContext,i)

        def AND(self):
            return self.getToken(RoboticsParser.AND, 0)
        def OR(self):
            return self.getToken(RoboticsParser.OR, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterLogicExpr" ):
                listener.enterLogicExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitLogicExpr" ):
                listener.exitLogicExpr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitLogicExpr" ):
                return visitor.visitLogicExpr(self)
            else:
                return visitor.visitChildren(self)


    class AtomExprContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a RoboticsParser.ExpressionContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def primary(self):
            return self.getTypedRuleContext(RoboticsParser.PrimaryContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterAtomExpr" ):
                listener.enterAtomExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitAtomExpr" ):
                listener.exitAtomExpr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAtomExpr" ):
                return visitor.visitAtomExpr(self)
            else:
                return visitor.visitChildren(self)


    class MulDivExprContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a RoboticsParser.ExpressionContext
            super().__init__(parser)
            self.left = None # ExpressionContext
            self.op = None # Token
            self.right = None # ExpressionContext
            self.copyFrom(ctx)

        def expression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(RoboticsParser.ExpressionContext)
            else:
                return self.getTypedRuleContext(RoboticsParser.ExpressionContext,i)

        def STAR(self):
            return self.getToken(RoboticsParser.STAR, 0)
        def SLASH(self):
            return self.getToken(RoboticsParser.SLASH, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterMulDivExpr" ):
                listener.enterMulDivExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitMulDivExpr" ):
                listener.exitMulDivExpr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMulDivExpr" ):
                return visitor.visitMulDivExpr(self)
            else:
                return visitor.visitChildren(self)



    def expression(self, _p:int=0):
        _parentctx = self._ctx
        _parentState = self.state
        localctx = RoboticsParser.ExpressionContext(self, self._ctx, _parentState)
        _prevctx = localctx
        _startState = 52
        self.enterRecursionRule(localctx, 52, self.RULE_expression, _p)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            localctx = RoboticsParser.AtomExprContext(self, localctx)
            self._ctx = localctx
            _prevctx = localctx

            self.state = 266
            self.primary()
            self._ctx.stop = self._input.LT(-1)
            self.state = 282
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,18,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    if self._parseListeners is not None:
                        self.triggerExitRuleEvent()
                    _prevctx = localctx
                    self.state = 280
                    self._errHandler.sync(self)
                    la_ = self._interp.adaptivePredict(self._input,17,self._ctx)
                    if la_ == 1:
                        localctx = RoboticsParser.MulDivExprContext(self, RoboticsParser.ExpressionContext(self, _parentctx, _parentState))
                        localctx.left = _prevctx
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expression)
                        self.state = 268
                        if not self.precpred(self._ctx, 4):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 4)")
                        self.state = 269
                        localctx.op = self._input.LT(1)
                        _la = self._input.LA(1)
                        if not(_la==45 or _la==46):
                            localctx.op = self._errHandler.recoverInline(self)
                        else:
                            self._errHandler.reportMatch(self)
                            self.consume()
                        self.state = 270
                        localctx.right = self.expression(5)
                        pass

                    elif la_ == 2:
                        localctx = RoboticsParser.AddSubExprContext(self, RoboticsParser.ExpressionContext(self, _parentctx, _parentState))
                        localctx.left = _prevctx
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expression)
                        self.state = 271
                        if not self.precpred(self._ctx, 3):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 3)")
                        self.state = 272
                        localctx.op = self._input.LT(1)
                        _la = self._input.LA(1)
                        if not(_la==43 or _la==44):
                            localctx.op = self._errHandler.recoverInline(self)
                        else:
                            self._errHandler.reportMatch(self)
                            self.consume()
                        self.state = 273
                        localctx.right = self.expression(4)
                        pass

                    elif la_ == 3:
                        localctx = RoboticsParser.CompExprContext(self, RoboticsParser.ExpressionContext(self, _parentctx, _parentState))
                        localctx.left = _prevctx
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expression)
                        self.state = 274
                        if not self.precpred(self._ctx, 2):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 2)")
                        self.state = 275
                        localctx.op = self._input.LT(1)
                        _la = self._input.LA(1)
                        if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 8658654068736) != 0)):
                            localctx.op = self._errHandler.recoverInline(self)
                        else:
                            self._errHandler.reportMatch(self)
                            self.consume()
                        self.state = 276
                        localctx.right = self.expression(3)
                        pass

                    elif la_ == 4:
                        localctx = RoboticsParser.LogicExprContext(self, RoboticsParser.ExpressionContext(self, _parentctx, _parentState))
                        localctx.left = _prevctx
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expression)
                        self.state = 277
                        if not self.precpred(self._ctx, 1):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 1)")
                        self.state = 278
                        localctx.op = self._input.LT(1)
                        _la = self._input.LA(1)
                        if not(_la==35 or _la==36):
                            localctx.op = self._errHandler.recoverInline(self)
                        else:
                            self._errHandler.reportMatch(self)
                            self.consume()
                        self.state = 279
                        localctx.right = self.expression(2)
                        pass

             
                self.state = 284
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,18,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.unrollRecursionContexts(_parentctx)
        return localctx


    class PrimaryContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return RoboticsParser.RULE_primary

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class IntLitContext(PrimaryContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a RoboticsParser.PrimaryContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def INT(self):
            return self.getToken(RoboticsParser.INT, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterIntLit" ):
                listener.enterIntLit(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitIntLit" ):
                listener.exitIntLit(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitIntLit" ):
                return visitor.visitIntLit(self)
            else:
                return visitor.visitChildren(self)


    class VarRefContext(PrimaryContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a RoboticsParser.PrimaryContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def ID(self):
            return self.getToken(RoboticsParser.ID, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterVarRef" ):
                listener.enterVarRef(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitVarRef" ):
                listener.exitVarRef(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitVarRef" ):
                return visitor.visitVarRef(self)
            else:
                return visitor.visitChildren(self)


    class DurLitContext(PrimaryContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a RoboticsParser.PrimaryContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def literalDuration(self):
            return self.getTypedRuleContext(RoboticsParser.LiteralDurationContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDurLit" ):
                listener.enterDurLit(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDurLit" ):
                listener.exitDurLit(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitDurLit" ):
                return visitor.visitDurLit(self)
            else:
                return visitor.visitChildren(self)


    class ParenExprContext(PrimaryContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a RoboticsParser.PrimaryContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def expression(self):
            return self.getTypedRuleContext(RoboticsParser.ExpressionContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterParenExpr" ):
                listener.enterParenExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitParenExpr" ):
                listener.exitParenExpr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitParenExpr" ):
                return visitor.visitParenExpr(self)
            else:
                return visitor.visitChildren(self)



    def primary(self):

        localctx = RoboticsParser.PrimaryContext(self, self._ctx, self.state)
        self.enterRule(localctx, 54, self.RULE_primary)
        try:
            self.state = 292
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,19,self._ctx)
            if la_ == 1:
                localctx = RoboticsParser.IntLitContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 285
                self.match(RoboticsParser.INT)
                pass

            elif la_ == 2:
                localctx = RoboticsParser.DurLitContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 286
                self.literalDuration()
                pass

            elif la_ == 3:
                localctx = RoboticsParser.VarRefContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 287
                self.match(RoboticsParser.ID)
                pass

            elif la_ == 4:
                localctx = RoboticsParser.ParenExprContext(self, localctx)
                self.enterOuterAlt(localctx, 4)
                self.state = 288
                self.match(RoboticsParser.T__0)
                self.state = 289
                self.expression(0)
                self.state = 290
                self.match(RoboticsParser.T__1)
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx



    def sempred(self, localctx:RuleContext, ruleIndex:int, predIndex:int):
        if self._predicates == None:
            self._predicates = dict()
        self._predicates[26] = self.expression_sempred
        pred = self._predicates.get(ruleIndex, None)
        if pred is None:
            raise Exception("No predicate with index:" + str(ruleIndex))
        else:
            return pred(localctx, predIndex)

    def expression_sempred(self, localctx:ExpressionContext, predIndex:int):
            if predIndex == 0:
                return self.precpred(self._ctx, 4)
         

            if predIndex == 1:
                return self.precpred(self._ctx, 3)
         

            if predIndex == 2:
                return self.precpred(self._ctx, 2)
         

            if predIndex == 3:
                return self.precpred(self._ctx, 1)
         




