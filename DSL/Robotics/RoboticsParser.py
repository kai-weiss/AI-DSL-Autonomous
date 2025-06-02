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
        4,1,21,89,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,2,4,7,4,2,5,7,5,2,6,7,
        6,2,7,7,7,2,8,7,8,2,9,7,9,1,0,5,0,22,8,0,10,0,12,0,25,9,0,1,0,1,
        0,1,1,1,1,1,1,3,1,32,8,1,1,2,1,2,1,2,1,2,1,2,1,2,1,3,1,3,1,3,5,3,
        43,8,3,10,3,12,3,46,9,3,1,4,1,4,1,4,1,4,1,4,1,4,1,4,1,4,1,4,1,4,
        1,4,1,4,3,4,60,8,4,1,5,1,5,1,5,1,5,1,5,3,5,67,8,5,1,6,1,6,1,6,1,
        6,1,6,1,6,1,6,1,7,1,7,1,7,1,7,1,8,1,8,1,8,1,8,1,8,1,8,1,9,1,9,1,
        9,1,9,0,0,10,0,2,4,6,8,10,12,14,16,18,0,0,86,0,23,1,0,0,0,2,31,1,
        0,0,0,4,33,1,0,0,0,6,44,1,0,0,0,8,59,1,0,0,0,10,61,1,0,0,0,12,68,
        1,0,0,0,14,75,1,0,0,0,16,79,1,0,0,0,18,85,1,0,0,0,20,22,3,2,1,0,
        21,20,1,0,0,0,22,25,1,0,0,0,23,21,1,0,0,0,23,24,1,0,0,0,24,26,1,
        0,0,0,25,23,1,0,0,0,26,27,5,0,0,1,27,1,1,0,0,0,28,32,3,4,2,0,29,
        32,3,10,5,0,30,32,3,16,8,0,31,28,1,0,0,0,31,29,1,0,0,0,31,30,1,0,
        0,0,32,3,1,0,0,0,33,34,5,1,0,0,34,35,5,19,0,0,35,36,5,10,0,0,36,
        37,3,6,3,0,37,38,5,11,0,0,38,5,1,0,0,0,39,40,3,8,4,0,40,41,5,13,
        0,0,41,43,1,0,0,0,42,39,1,0,0,0,43,46,1,0,0,0,44,42,1,0,0,0,44,45,
        1,0,0,0,45,7,1,0,0,0,46,44,1,0,0,0,47,48,5,4,0,0,48,49,5,14,0,0,
        49,60,3,18,9,0,50,51,5,5,0,0,51,52,5,14,0,0,52,60,3,18,9,0,53,54,
        5,6,0,0,54,55,5,14,0,0,55,60,3,18,9,0,56,57,5,7,0,0,57,58,5,14,0,
        0,58,60,5,17,0,0,59,47,1,0,0,0,59,50,1,0,0,0,59,53,1,0,0,0,59,56,
        1,0,0,0,60,9,1,0,0,0,61,62,5,2,0,0,62,63,3,14,7,0,63,64,5,9,0,0,
        64,66,3,14,7,0,65,67,3,12,6,0,66,65,1,0,0,0,66,67,1,0,0,0,67,11,
        1,0,0,0,68,69,5,10,0,0,69,70,5,8,0,0,70,71,5,14,0,0,71,72,3,18,9,
        0,72,73,5,13,0,0,73,74,5,11,0,0,74,13,1,0,0,0,75,76,5,19,0,0,76,
        77,5,15,0,0,77,78,5,19,0,0,78,15,1,0,0,0,79,80,5,3,0,0,80,81,5,19,
        0,0,81,82,5,12,0,0,82,83,5,16,0,0,83,84,5,13,0,0,84,17,1,0,0,0,85,
        86,5,17,0,0,86,87,5,18,0,0,87,19,1,0,0,0,5,23,31,44,59,66
    ]

class RoboticsParser ( Parser ):

    grammarFileName = "Robotics.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'COMPONENT'", "'CONNECT'", "'PROPERTY'", 
                     "'period'", "'deadline'", "'WCET'", "'priority'", "'latency_budget'", 
                     "'->'", "'{'", "'}'", "':'", "';'", "'='", "'.'", "<INVALID>", 
                     "<INVALID>", "'ms'" ]

    symbolicNames = [ "<INVALID>", "COMPONENT", "CONNECT", "PROPERTY", "PERIOD", 
                      "DEADLINE", "WCET", "PRIORITY", "LATENCY_BUDGET", 
                      "ARROW", "LBRACE", "RBRACE", "COLON", "SEMI", "EQUAL", 
                      "DOT", "STRING", "INT", "UNIT_MS", "ID", "WS", "LINE_COMMENT" ]

    RULE_file = 0
    RULE_statement = 1
    RULE_componentDecl = 2
    RULE_componentBody = 3
    RULE_componentAttr = 4
    RULE_connectDecl = 5
    RULE_connectBody = 6
    RULE_endpoint = 7
    RULE_propertyDecl = 8
    RULE_duration = 9

    ruleNames =  [ "file", "statement", "componentDecl", "componentBody", 
                   "componentAttr", "connectDecl", "connectBody", "endpoint", 
                   "propertyDecl", "duration" ]

    EOF = Token.EOF
    COMPONENT=1
    CONNECT=2
    PROPERTY=3
    PERIOD=4
    DEADLINE=5
    WCET=6
    PRIORITY=7
    LATENCY_BUDGET=8
    ARROW=9
    LBRACE=10
    RBRACE=11
    COLON=12
    SEMI=13
    EQUAL=14
    DOT=15
    STRING=16
    INT=17
    UNIT_MS=18
    ID=19
    WS=20
    LINE_COMMENT=21

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
            self.state = 23
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & 14) != 0):
                self.state = 20
                self.statement()
                self.state = 25
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 26
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
            self.state = 31
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [1]:
                self.enterOuterAlt(localctx, 1)
                self.state = 28
                self.componentDecl()
                pass
            elif token in [2]:
                self.enterOuterAlt(localctx, 2)
                self.state = 29
                self.connectDecl()
                pass
            elif token in [3]:
                self.enterOuterAlt(localctx, 3)
                self.state = 30
                self.propertyDecl()
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
            self.state = 33
            self.match(RoboticsParser.COMPONENT)
            self.state = 34
            self.match(RoboticsParser.ID)
            self.state = 35
            self.match(RoboticsParser.LBRACE)
            self.state = 36
            self.componentBody()
            self.state = 37
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
            self.state = 44
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & 240) != 0):
                self.state = 39
                self.componentAttr()
                self.state = 40
                self.match(RoboticsParser.SEMI)
                self.state = 46
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
            self.state = 59
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [4]:
                self.enterOuterAlt(localctx, 1)
                self.state = 47
                self.match(RoboticsParser.PERIOD)
                self.state = 48
                self.match(RoboticsParser.EQUAL)
                self.state = 49
                self.duration()
                pass
            elif token in [5]:
                self.enterOuterAlt(localctx, 2)
                self.state = 50
                self.match(RoboticsParser.DEADLINE)
                self.state = 51
                self.match(RoboticsParser.EQUAL)
                self.state = 52
                self.duration()
                pass
            elif token in [6]:
                self.enterOuterAlt(localctx, 3)
                self.state = 53
                self.match(RoboticsParser.WCET)
                self.state = 54
                self.match(RoboticsParser.EQUAL)
                self.state = 55
                self.duration()
                pass
            elif token in [7]:
                self.enterOuterAlt(localctx, 4)
                self.state = 56
                self.match(RoboticsParser.PRIORITY)
                self.state = 57
                self.match(RoboticsParser.EQUAL)
                self.state = 58
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
            self.state = 61
            self.match(RoboticsParser.CONNECT)
            self.state = 62
            localctx.src = self.endpoint()
            self.state = 63
            self.match(RoboticsParser.ARROW)
            self.state = 64
            localctx.dst = self.endpoint()
            self.state = 66
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==10:
                self.state = 65
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
            self.state = 68
            self.match(RoboticsParser.LBRACE)
            self.state = 69
            self.match(RoboticsParser.LATENCY_BUDGET)
            self.state = 70
            self.match(RoboticsParser.EQUAL)
            self.state = 71
            self.duration()
            self.state = 72
            self.match(RoboticsParser.SEMI)
            self.state = 73
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
            self.comp = None # Token
            self.port = None # Token

        def DOT(self):
            return self.getToken(RoboticsParser.DOT, 0)

        def ID(self, i:int=None):
            if i is None:
                return self.getTokens(RoboticsParser.ID)
            else:
                return self.getToken(RoboticsParser.ID, i)

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
            self.state = 75
            localctx.comp = self.match(RoboticsParser.ID)
            self.state = 76
            self.match(RoboticsParser.DOT)
            self.state = 77
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

        def getRuleIndex(self):
            return RoboticsParser.RULE_propertyDecl

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterPropertyDecl" ):
                listener.enterPropertyDecl(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitPropertyDecl" ):
                listener.exitPropertyDecl(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPropertyDecl" ):
                return visitor.visitPropertyDecl(self)
            else:
                return visitor.visitChildren(self)




    def propertyDecl(self):

        localctx = RoboticsParser.PropertyDeclContext(self, self._ctx, self.state)
        self.enterRule(localctx, 16, self.RULE_propertyDecl)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 79
            self.match(RoboticsParser.PROPERTY)
            self.state = 80
            self.match(RoboticsParser.ID)
            self.state = 81
            self.match(RoboticsParser.COLON)
            self.state = 82
            self.match(RoboticsParser.STRING)
            self.state = 83
            self.match(RoboticsParser.SEMI)
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
        self.enterRule(localctx, 18, self.RULE_duration)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 85
            self.match(RoboticsParser.INT)
            self.state = 86
            self.match(RoboticsParser.UNIT_MS)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx





