import sys
from rlite_lexer import init_lexer, lex, tableOfSymb

numRow = 1
len_tableOfSymb = 0
indt = 0
stepIndt = 2

def nextIndt():
    global indt
    indt += stepIndt
    return ' ' * indt

def predIndt():
    global indt
    indt -= stepIndt
    return ' ' * indt

def getSymb():
    if numRow > len_tableOfSymb:
        failParse('неочікуваний кінець програми', ('', '', numRow, 'кінець'))
    return tableOfSymb[numRow]

def peek_tok(offset=0):
    idx = numRow + offset
    if idx <= len_tableOfSymb:
        return tableOfSymb[idx]
    return (0, '', 'EOF', '')

def parseToken(lexeme, token):
    global numRow
    indent = nextIndt()
    if numRow > len_tableOfSymb:
        failParse('неочікуваний кінець програми', (lexeme, token, numRow, ''))
    
    numLine, lex, tok, _ = getSymb()
    numRow += 1
    
    if (lex, tok) == (lexeme, token) or (tok == token and lexeme == ''):
        print(indent + f'parseToken: В рядку {numLine} токен {lex, tok}')
        predIndt()
        return True
    else:
        failParse('невідповідність токенів', (numLine, lex, tok, f'{lexeme} ({token})'))

def failParse(msg, err_tuple):
    if msg == 'неочікуваний кінець програми':
        lexeme, token, numRow, _ = err_tuple
        print(f"Parser ERROR: \n\t Неочікуваний кінець програми. Очікувалось {lexeme} ({token})")
        sys.exit(1001)
    else:
        numLine, lex, tok, expected = err_tuple
        print(f"Parser ERROR: \n\t В рядку {numLine} неочікуваний елемент ({lex}, {tok}).\n\t Очікувався: {expected}.\n\t Причина: {msg}")
        sys.exit(1)


def is_type_start():
    """Перевіряє, чи починається поточна позиція з data_type."""
    t0 = peek_tok(0)
    if t0[2] == 'keyword' and t0[1] in ('int', 'float', 'bool', 'string'):
        return True
    if t0[2] == 'id':
        t1 = peek_tok(1)
        if t1[2] == 'id': return True
        t2, t3 = peek_tok(2), peek_tok(3)
        if t1[1] == '[' and t2[1] == ']' and t3[2] == 'id': return True
    return False

def is_assignment():
    """Перевіряє, чи є поточна позиція операцією assignment (id <- або id[...] <-)."""
    t0 = peek_tok(0)
    if t0[2] != 'id': return False
    t1 = peek_tok(1)
    if t1[1] == '<-': return True
    if t1[1] == '[':
        idx = 2
        depth = 1
        while numRow + idx <= len_tableOfSymb and depth > 0:
            t = peek_tok(idx)
            if t[1] == '[': depth += 1
            elif t[1] == ']': depth -= 1
            idx += 1
        if peek_tok(idx)[1] == '<-': return True
    return False


def parseProgram():
    print('parseProgram():')
    while numRow <= len_tableOfSymb:
        parseStatement()
    print('\nParser: Синтаксичний аналіз завершився успішно')
    return True

def parseStatement():
    indent = nextIndt()
    print(indent + 'parseStatement():')
    t0 = peek_tok(0)

    if t0[1] == 'type': parseTypeDeclaration()
    elif t0[1] == 'const': parseConstantDeclaration()
    elif t0[1] == 'if': parseIfStatement()
    elif t0[1] == 'while': parseWhileStatement()
    elif t0[1] == 'return': parseReturnStatement()
    elif t0[1] == 'read': parseInputStatement()
    elif t0[1] == 'print': parseOutputStatement()
    elif is_type_start():
        parseDeclarationRouter()
    elif is_assignment():
        parseAssignment()
    else:
        parseExpressionStatement()

    predIndt()
    return True

def parseDeclarationRouter():
    """Розподіляє на function_declaration або variable_declaration"""
    parseDataType()
    parseToken('', 'id')
    t0 = peek_tok(0)
    if t0[1] == '<-' and peek_tok(1)[1] == 'function':
        parseToken('<-', 'assign_op')
        parseToken('function', 'keyword')
        parseToken('(', 'par_op')
        if peek_tok(0)[1] != ')':
            parseParameterList()
        parseToken(')', 'par_op')
        parseBlock()
    else:
        if peek_tok(0)[1] == '<-':
            parseToken('<-', 'assign_op')
            parseExpression()
        parseToken(';', 'punct')

def parseVariableDeclaration():
    pass

def parseConstantDeclaration():
    parseToken('const', 'keyword')
    parseDataType()
    parseToken('', 'id')
    parseToken('<-', 'assign_op')
    parseExpression()
    parseToken(';', 'punct')

def parseTypeDeclaration():
    parseToken('type', 'keyword')
    parseToken('', 'id')
    parseToken('<-', 'assign_op')
    parseBaseType()
    parseToken(';', 'punct')

def parseDataType():
    t0 = peek_tok(0)
    t1 = peek_tok(1)
    if t1[1] == '[':
        parseArrayType()
    else:
        parseBaseType()

def parseArrayType():
    parseBaseType()
    parseToken('[', 'brack_op')
    parseToken(']', 'brack_op')

def parseBaseType():
    t0 = peek_tok(0)
    if t0[2] == 'keyword' and t0[1] in ('int', 'float', 'bool', 'string'):
        parseScalarType()
    else:
        parseToken('', 'id')

def parseScalarType():
    t0 = peek_tok(0)
    parseToken(t0[1], 'keyword')

# --- Інструкції ---

def parseAssignment():
    parseAssignable()
    parseToken('<-', 'assign_op')
    parseExpression()
    parseToken(';', 'punct')

def parseAssignable():
    parseToken('', 'id')
    if peek_tok(0)[1] == '[':
        parseToken('[', 'brack_op')
        parseExpression()
        parseToken(']', 'brack_op')

def parseInputStatement():
    parseToken('read', 'keyword')
    parseToken('(', 'par_op')
    parseInputList()
    parseToken(')', 'par_op')
    parseToken(';', 'punct')

def parseInputList():
    parseAssignable()
    while peek_tok(0)[1] == ',':
        parseToken(',', 'punct')
        parseAssignable()

def parseOutputStatement():
    parseToken('print', 'keyword')
    parseToken('(', 'par_op')
    if peek_tok(0)[1] != ')':
        parseArgumentList()
    parseToken(')', 'par_op')
    parseToken(';', 'punct')

def parseIfStatement():
    parseToken('if', 'keyword')
    parseToken('(', 'par_op')
    parseExpression()
    parseToken(')', 'par_op')
    parseBlock()
    if peek_tok(0)[1] == 'else':
        parseElseClause()

def parseElseClause():
    parseToken('else', 'keyword')
    if peek_tok(0)[1] == 'if':
        parseIfStatement()
    else:
        parseBlock()

def parseWhileStatement():
    parseToken('while', 'keyword')
    parseToken('(', 'par_op')
    parseExpression()
    parseToken(')', 'par_op')
    parseBlock()

def parseBlock():
    parseToken('{', 'brace_op')
    while peek_tok(0)[1] != '}':
        parseStatement()
    parseToken('}', 'brace_op')

def parseParameterList():
    parseParameter()
    while peek_tok(0)[1] == ',':
        parseToken(',', 'punct')
        parseParameter()

def parseParameter():
    parseDataType()
    parseToken('', 'id')

def parseReturnStatement():
    parseToken('return', 'keyword')
    parseExpression()
    parseToken(';', 'punct')

def parseArgumentList():
    parseExpression()
    while peek_tok(0)[1] == ',':
        parseToken(',', 'punct')
        parseExpression()

def parseExpressionStatement():
    parseExpression()
    parseToken(';', 'punct')


def parseExpression():
    parseLogicalOrExpression()

def parseLogicalOrExpression():
    parseLogicalAndExpression()
    while peek_tok(0)[1] == '|':
        parseToken('|', 'logic_op')
        parseLogicalAndExpression()

def parseLogicalAndExpression():
    parseEqualityExpression()
    while peek_tok(0)[1] == '&':
        parseToken('&', 'logic_op')
        parseEqualityExpression()

def parseEqualityExpression():
    parseComparisonExpression()
    if peek_tok(0)[1] in ('==', '!='):
        parseToken(peek_tok(0)[1], 'rel_op')
        parseComparisonExpression()

def parseComparisonExpression():
    parseAdditiveExpression()
    if peek_tok(0)[1] in ('<=', '>=', '<', '>'):
        parseToken(peek_tok(0)[1], 'rel_op')
        parseAdditiveExpression()

def parseAdditiveExpression():
    indent = nextIndt()
    print(indent + 'parseAdditiveExpression():')
    parseMultiplicativeExpression()
    while peek_tok(0)[1] in ('+', '-'):
        parseToken(peek_tok(0)[1], 'add_op')
        parseMultiplicativeExpression()
    predIndt()

def parseMultiplicativeExpression():
    indent = nextIndt()
    print(indent + 'parseMultiplicativeExpression():')
    parseUnaryExpression()
    while peek_tok(0)[1] in ('*', '/'):
        parseToken(peek_tok(0)[1], 'mult_op')
        parseUnaryExpression()
    predIndt()

def parseUnaryExpression():
    t0 = peek_tok(0)
    if t0[1] in ('+', '-'):
        parseToken(t0[1], 'add_op')
        parseUnaryExpression()
    elif t0[1] == '!':
        parseToken('!', 'logic_op')
        parseUnaryExpression()
    else:
        parsePowerExpression()

def parsePowerExpression():
    indent = nextIndt()
    print(indent + 'parsePowerExpression():')
    parsePrimaryExpression()
    # Опціональний power_expression (правоасоціативність)
    if peek_tok(0)[1] == '^':
        parseToken('^', 'power_op')
        parseUnaryExpression()
    predIndt()

def parsePrimaryExpression():
    indent = nextIndt()
    print(indent + 'parsePrimaryExpression():')
    t0 = peek_tok(0)

    if t0[2] == 'keyword' and t0[1] in ('int', 'float', 'bool', 'string'):
        parseCastExpression()
    elif t0[1] == 'c':
        parseArrayLiteral()
    elif t0[2] == 'id':
        t1 = peek_tok(1)
        if t1[1] == '(':
            parseFunctionCall()
        elif t1[1] == '[':
            parseArrayAccess()
        else:
            parseToken('', 'id')
    elif t0[1] == '(':
        parseToken('(', 'par_op')
        parseExpression()
        parseToken(')', 'par_op')
    elif t0[2] in ('int', 'float', 'string', 'bool'):
        parseToken(t0[1], t0[2])
    else:
        failParse("очікувався первинний вираз", (t0[0], t0[1], t0[2], "ідентифікатор, літерал або '('"))
    predIndt()

def parseCastExpression():
    parseScalarType()
    parseToken('(', 'par_op')
    parseExpression()
    parseToken(')', 'par_op')

def parseArrayLiteral():
    parseToken('c', 'array_ctor')
    parseToken('(', 'par_op')
    if peek_tok(0)[1] != ')':
        parseArgumentList()
    parseToken(')', 'par_op')

def parseFunctionCall():
    parseToken('', 'id')
    parseToken('(', 'par_op')
    if peek_tok(0)[1] != ')':
        parseArgumentList()
    parseToken(')', 'par_op')

def parseArrayAccess():
    parseToken('', 'id')
    parseToken('[', 'brack_op')
    parseExpression()
    parseToken(']', 'brack_op')


if __name__ == '__main__':
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"Парсинг файлу: {filepath}\n")
            init_lexer(content)
            if lex():
                len_tableOfSymb = len(tableOfSymb)
                parseProgram()
        except FileNotFoundError:
            print(f"Файл {filepath} не знайдено.")
    else:
        print("Використання: python rlite_parser.py <шлях_до_файлу_rlite>")
