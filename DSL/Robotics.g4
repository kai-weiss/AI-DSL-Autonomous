grammar Robotics;

/* ─────────────
 *  PARSER RULES
 * ───────────── */
file            : statement* EOF ;               // entry-point
statement       : componentDecl
                | connectDecl
                | propertyDecl
                ;

componentDecl   : COMPONENT ID LBRACE componentBody RBRACE ;
componentBody   : ( componentAttr SEMI )* ;
componentAttr   : PERIOD    EQUAL duration
                | DEADLINE  EQUAL duration
                | WCET      EQUAL duration
                | PRIORITY  EQUAL INT
                ;

connectDecl     : CONNECT src=endpoint ARROW dst=endpoint connectBody? ;
connectBody     : LBRACE LATENCY_BUDGET EQUAL duration SEMI RBRACE ;
endpoint        : comp=ID DOT port=ID ;                    // e.g. CameraProcessing.output

propertyDecl    : PROPERTY ID COLON STRING SEMI ;

duration        : INT UNIT_MS ;

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

ID              : [A-Z_a-z] [A-Z_a-z0-9]* ;
WS              : [ \t\r\n]+      -> skip ;
LINE_COMMENT    : '//' ~[\r\n]*   -> skip ;
