import ply.lex as lex


tokens = (
    "DIR_INCLUDE",
    "DIR_DEFINE",
    "DIR_UNDEF",
    "DIR_IFDEF",
    "DIR_IFNDEF",
    "DIR_ELSE",
    "DIR_ENDIF",
    "DIR_ERROR",
    "DIR_WARNING",
    "COMENTARIO_C",
    "NEWLINE",
    "CODIGO",
)


def t_DIR_INCLUDE(t):
    r"\#[ \t]*include[ \t]+\"[^\"\n]+\""
    return t


def t_DIR_DEFINE(t):
    r"\#[ \t]*define[ \t]+[A-Za-z_][A-Za-z0-9_]*(\([^)]*\))?[^\n]*"
    return t


def t_DIR_UNDEF(t):
    r"\#[ \t]*undef[ \t]+[A-Za-z_][A-Za-z0-9_]*[^\n]*"
    return t


def t_DIR_IFDEF(t):
    r"\#[ \t]*ifdef[ \t]+[A-Za-z_][A-Za-z0-9_]*[^\n]*"
    return t


def t_DIR_IFNDEF(t):
    r"\#[ \t]*ifndef[ \t]+[A-Za-z_][A-Za-z0-9_]*[^\n]*"
    return t


def t_DIR_ELSE(t):
    r"\#[ \t]*else[^\n]*"
    return t


def t_DIR_ENDIF(t):
    r"\#[ \t]*endif[^\n]*"
    return t


def t_DIR_ERROR(t):
    r"\#[ \t]*error[^\n]*"
    return t


def t_DIR_WARNING(t):
    r"\#[ \t]*warning[^\n]*"
    return t


def t_COMENTARIO_C(t):
    r"//[^\n]*"
    return t


def t_NEWLINE(t):
    r"\r?\n"
    t.lexer.lineno += 1
    return t


def t_CODIGO(t):
    r"[^\r\n]+"
    return t


# No ignorar espacios para preservar el texto original
t_ignore = ""


def t_error(t):
    t.lexer.skip(1)


def build_lexer():
    return lex.lex()
