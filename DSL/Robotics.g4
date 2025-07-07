grammar Robotics;

/* ─────────────
 *  PARSER RULES
 * ───────────── */
file            : statement* EOF ;               // entry-point
statement       : componentDecl
                | connectDecl
                | propertyDecl
                | optimisationBlock
                | systemDecl
                | vehicleDecl
                | cpuDecl
                ;

componentDecl   : COMPONENT ID LBRACE componentBody RBRACE ;
componentBody   : ( componentAttr SEMI )* ;
componentAttr   : PERIOD    EQUAL duration
                | DEADLINE  EQUAL duration
                | WCET      EQUAL duration
                | PRIORITY  EQUAL INT
                ;

connectDecl     : CONNECT (ID COLON)? src=endpoint ARROW dst=endpoint connectBody? ;
connectBody     : LBRACE LATENCY_BUDGET EQUAL duration SEMI RBRACE ;
endpoint        : comp=dottedId DOT port=ID ;                    // e.g. CameraProcessing.output

propertyDecl    : PROPERTY ID COLON STRING SEMI                # propertyString
                | PROPERTY ID LBRACE propertyField* RBRACE    # propertyBlock
                ;

vehicleDecl     : VEHICLE ID LBRACE componentDecl* RBRACE ;

cpuDecl         : CPU LBRACE cpuAttr* RBRACE ;
cpuAttr         : ID EQUAL (INT | ID) SEMI ;

systemDecl      : SYSTEM ID LBRACE statement* RBRACE ;

propertyField   : ID EQUAL propertyValue SEMI ;
propertyValue   : duration
                | dottedId
                | ID
                ;

dottedId        : ID (DOT ID)* ;

duration        : INT UNIT_MS ;

/* Optimization Block */
optimisationBlock
    : OPTIMISATION '{'
          VARIABLES '{' variableDecl+ '}'
          OBJECTIVES '{' objectiveDecl+ '}'
          CONSTRAINTS '{' constraintDecl+ '}'
      '}'
    ;

variableDecl
    : targetRef '.' attrName 'range' rangeSpec ';'
    ;

targetRef
    : dottedId                          # componentRef
    | '(' connectionRef ')'             # connectionRefWrapped
    ;

connectionRef
    : dottedId '.' ID '->' dottedId '.' ID   // Cam.out -> Planner.in
    ;

attrName
    : PERIOD
    | DEADLINE
    | WCET
    | PRIORITY
    | LATENCY_BUDGET
    | ID
    ;

rangeSpec
    : literalDuration '..' literalDuration
    ;

objectiveDecl
    : (MINIMISE | MAXIMISE) ID ';'
    ;

constraintDecl
    : 'assert' expression ';'
    ;

literalDuration
    : INT 'ms'
    ;

expression
    : primary                          # atomExpr
    | left=expression op=(STAR|SLASH) right=expression   # mulDivExpr
    | left=expression op=(PLUS|MINUS) right=expression   # addSubExpr
    | left=expression op=(LT|LE|GT|GE|EQ|NEQ) right=expression # compExpr
    | left=expression op=(AND|OR)  right=expression      # logicExpr
    ;

primary
    : INT                                  # intLit
    | literalDuration                      # durLit
    | ID                                # varRef
    | '(' expression ')'                   # parenExpr
    ;

/* ────────────
 *  LEXER RULES
 * ──────────── */
COMPONENT       : 'COMPONENT' ;
CONNECT         : 'CONNECT' ;
PROPERTY        : 'PROPERTY' ;

PERIOD          : 'period' ;
DEADLINE        : 'deadline' ;
WCET            : 'WCET' ;
PRIORITY        : 'priority' ;
LATENCY_BUDGET  : 'latency_budget' ;

SYSTEM          : 'SYSTEM' ;
VEHICLE         : 'VEHICLE' ;
CPU             : 'CPU' ;

ARROW           : '->' ;
LBRACE          : '{' ;
RBRACE          : '}' ;
COLON           : ':' ;
SEMI            : ';' ;
EQUAL           : '=' ;
DOT             : '.' ;

STRING          : '"' ( ~["\\] | '\\' . )* '"' ;
INT             : [0-9]+ ;
UNIT_MS         : 'ms' ;

WS              : [ \t\r\n]+      -> skip ;
LINE_COMMENT    : '//' ~[\r\n]*   -> skip ;

OPTIMISATION : 'OPTIMISATION';
VARIABLES    : 'VARIABLES';
OBJECTIVES   : 'OBJECTIVES';
CONSTRAINTS  : 'CONSTRAINTS';
MINIMISE     : 'minimise' | 'minimize';
MAXIMISE     : 'maximise' | 'maximize';
RANGE        : 'range'   ;
ASSERT       : 'assert'  ;
AND          : '&&';
OR           : '||';
EQ           : '==';
NEQ          : '!=';
LE           : '<=';
GE           : '>=';
LT           : '<';
GT           : '>';
PLUS         : '+';
MINUS        : '-';
STAR         : '*';
SLASH        : '/';
ID           : [A-Z_a-z] [A-Z_a-z0-9]* ;
