import sys
from rlite_lexer import init_lexer, lex, tableOfSymb

numRow = 1
len_tableOfSymb = 0
indt = 0
stepIndt = 2

tabName = {'univ': {'declIn': '-'}}
current_context = 'univ'

def insert(cxt, name, kind, type_, val, nParam='-'):
    if name in tabName[cxt]:
        return False
    tabName[cxt][name] = (len(tabName[cxt]), kind, type_, val, nParam)
    return True

def findName(name, cxt):
    curr = cxt
    while curr != '-':
        if name in tabName[curr]:
            return tabName[curr][name]
        curr = tabName[curr].get('declIn', '-')
    return None

def setAssigned(name, cxt):
    curr = cxt
    while curr != '-':
        if name in tabName[curr]:
            attr = list(tabName[curr][name])
            attr[3] = 'assigned'
            tabName[curr][name] = tuple(attr)
            return True
        curr = tabName[curr].get('declIn', '-')
    return False

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

def failSem(msg, err_tuple):
    numLine, lex, tok = err_tuple
    print(f"Semantic ERROR: \n\t В рядку {numLine} помилка: {msg} ({lex}, {tok})")
    sys.exit(2)

def getTypeOp(lType, op, rType):
    if lType == 'type_error' or rType == 'type_error':
        return 'type_error'
    if op == '<-':
        if lType == rType: return 'void'
        if lType == 'float' and rType == 'int': return 'void'
        return 'type_error'
    typesAreSame = (lType == rType)
    typesArithm = lType in ('int', 'float') and rType in ('int', 'float')
    if op in ('+', '-', '*', '/', '^'):
        if not typesArithm: return 'type_error'
        if lType == 'float' or rType == 'float': return 'float'
        return 'int'
    if op in ('<', '<=', '>', '>=', '==', '!='):
        if typesArithm or typesAreSame: return 'bool'
        return 'type_error'
    if op in ('&', '|'):
        if lType == 'bool' and rType == 'bool': return 'bool'
        return 'type_error'
    return 'type_error'

def is_type_start():
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
    global current_context
    type_val = parseDataType()
    t_id = peek_tok(0)
    id_val = t_id[1]
    parseToken('', 'id')
    t0 = peek_tok(0)
    
    if t0[1] == '<-' and peek_tok(1)[1] == 'function':
        parseToken('<-', 'assign_op')
        parseToken('function', 'keyword')
        
        if not insert(current_context, id_val, 'func', type_val, '-', '-'):
            failSem('повторне оголошення', (t_id[0], t_id[1], t_id[2]))
            
        tabName[id_val] = {'declIn': current_context}
        prev_context = current_context
        current_context = id_val
        
        parseToken('(', 'par_op')
        if peek_tok(0)[1] != ')':
            parseParameterList()
        parseToken(')', 'par_op')
        parseBlock()
        
        current_context = prev_context
    else:
        if not insert(current_context, id_val, 'var', type_val, 'undefined'):
            failSem('повторне оголошення', (t_id[0], t_id[1], t_id[2]))
        if peek_tok(0)[1] == '<-':
            t_ass = peek_tok(0)
            parseToken('<-', 'assign_op')
            rType = parseExpression()
            if getTypeOp(type_val, '<-', rType) == 'type_error':
                failSem('невідповідність типів присвоєння', (t_ass[0], t_ass[1], t_ass[2]))
            setAssigned(id_val, current_context)
        parseToken(';', 'punct')

def parseVariableDeclaration():
    pass

def parseConstantDeclaration():
    parseToken('const', 'keyword')
    type_val = parseDataType()
    t_id = peek_tok(0)
    id_val = t_id[1]
    parseToken('', 'id')
    t_ass = peek_tok(0)
    parseToken('<-', 'assign_op')
    rType = parseExpression()
    
    if getTypeOp(type_val, '<-', rType) == 'type_error':
        failSem('невідповідність типів присвоєння', (t_ass[0], t_ass[1], t_ass[2]))
        
    if not insert(current_context, id_val, 'const', type_val, 'assigned'):
        failSem('повторне оголошення', (t_id[0], t_id[1], t_id[2]))
        
    parseToken(';', 'punct')

def parseTypeDeclaration():
    parseToken('type', 'keyword')
    t_id = peek_tok(0)
    id_val = t_id[1]
    parseToken('', 'id')
    parseToken('<-', 'assign_op')
    type_val = parseBaseType()
    
    if not insert(current_context, id_val, 'type', type_val, 'assigned'):
        failSem('повторне оголошення', (t_id[0], t_id[1], t_id[2]))
        
    parseToken(';', 'punct')

def parseDataType():
    t0 = peek_tok(0)
    t1 = peek_tok(1)
    if t1[1] == '[':
        return parseArrayType()
    else:
        return parseBaseType()

def parseArrayType():
    bt = parseBaseType()
    parseToken('[', 'brack_op')
    parseToken(']', 'brack_op')
    return bt + '[]'

def parseBaseType():
    t0 = peek_tok(0)
    if t0[2] == 'keyword' and t0[1] in ('int', 'float', 'bool', 'string'):
        return parseScalarType()
    else:
        parseToken('', 'id')
        return t0[1]

def parseScalarType():
    t0 = peek_tok(0)
    parseToken(t0[1], 'keyword')
    return t0[1]

def parseAssignment():
    t0 = peek_tok(0)
    attr = findName(t0[1], current_context)
    if not attr:
        failSem('неоголошена змінна', (t0[0], t0[1], t0[2]))
    lType = attr[2]
    
    parseAssignable()
    t_ass = peek_tok(0)
    parseToken('<-', 'assign_op')
    rType = parseExpression()
    
    if getTypeOp(lType, '<-', rType) == 'type_error':
        failSem('невідповідність типів присвоєння', (t_ass[0], t_ass[1], t_ass[2]))
        
    setAssigned(t0[1], current_context)
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
    t0 = peek_tok(0)
    parseAssignable()
    attr = findName(t0[1], current_context)
    if not attr: 
        failSem('неоголошена змінна', (t0[0], t0[1], t0[2]))
    setAssigned(t0[1], current_context)
    
    while peek_tok(0)[1] == ',':
        parseToken(',', 'punct')
        t_next = peek_tok(0)
        parseAssignable()
        attr_next = findName(t_next[1], current_context)
        if not attr_next: 
            failSem('неоголошена змінна', (t_next[0], t_next[1], t_next[2]))
        setAssigned(t_next[1], current_context)

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
    t_expr = peek_tok(0)
    eType = parseExpression()
    if eType != 'bool':
        failSem('умова має бути типу bool', (t_expr[0], t_expr[1], t_expr[2]))
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
    t_expr = peek_tok(0)
    eType = parseExpression()
    if eType != 'bool':
        failSem('умова має бути типу bool', (t_expr[0], t_expr[1], t_expr[2]))
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
    type_val = parseDataType()
    t_id = peek_tok(0)
    id_val = t_id[1]
    parseToken('', 'id')
    if not insert(current_context, id_val, 'var', type_val, 'assigned'):
        failSem('повторне оголошення параметра', (t_id[0], t_id[1], t_id[2]))

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
    return parseLogicalOrExpression()

def parseLogicalOrExpression():
    lType = parseLogicalAndExpression()
    while peek_tok(0)[1] == '|':
        t_op = peek_tok(0)
        parseToken('|', 'logic_op')
        rType = parseLogicalAndExpression()
        lType = getTypeOp(lType, '|', rType)
        if lType == 'type_error':
            failSem('невідповідність типів', (t_op[0], t_op[1], t_op[2]))
    return lType

def parseLogicalAndExpression():
    lType = parseEqualityExpression()
    while peek_tok(0)[1] == '&':
        t_op = peek_tok(0)
        parseToken('&', 'logic_op')
        rType = parseEqualityExpression()
        lType = getTypeOp(lType, '&', rType)
        if lType == 'type_error':
            failSem('невідповідність типів', (t_op[0], t_op[1], t_op[2]))
    return lType

def parseEqualityExpression():
    lType = parseComparisonExpression()
    if peek_tok(0)[1] in ('==', '!='):
        t_op = peek_tok(0)
        parseToken(t_op[1], 'rel_op')
        rType = parseComparisonExpression()
        lType = getTypeOp(lType, t_op[1], rType)
        if lType == 'type_error':
            failSem('невідповідність типів', (t_op[0], t_op[1], t_op[2]))
    return lType

def parseComparisonExpression():
    lType = parseAdditiveExpression()
    if peek_tok(0)[1] in ('<=', '>=', '<', '>'):
        t_op = peek_tok(0)
        parseToken(t_op[1], 'rel_op')
        rType = parseAdditiveExpression()
        lType = getTypeOp(lType, t_op[1], rType)
        if lType == 'type_error':
            failSem('невідповідність типів', (t_op[0], t_op[1], t_op[2]))
    return lType

def parseAdditiveExpression():
    indent = nextIndt()
    print(indent + 'parseAdditiveExpression():')
    lType = parseMultiplicativeExpression()
    while peek_tok(0)[1] in ('+', '-'):
        t_op = peek_tok(0)
        parseToken(t_op[1], 'add_op')
        rType = parseMultiplicativeExpression()
        lType = getTypeOp(lType, t_op[1], rType)
        if lType == 'type_error':
            failSem('невідповідність типів', (t_op[0], t_op[1], t_op[2]))
    predIndt()
    return lType

def parseMultiplicativeExpression():
    indent = nextIndt()
    print(indent + 'parseMultiplicativeExpression():')
    lType = parseUnaryExpression()
    while peek_tok(0)[1] in ('*', '/'):
        t_op = peek_tok(0)
        parseToken(t_op[1], 'mult_op')
        rType = parseUnaryExpression()
        lType = getTypeOp(lType, t_op[1], rType)
        if lType == 'type_error':
            failSem('невідповідність типів', (t_op[0], t_op[1], t_op[2]))
    predIndt()
    return lType

def parseUnaryExpression():
    t0 = peek_tok(0)
    if t0[1] in ('+', '-'):
        parseToken(t0[1], 'add_op')
        rType = parseUnaryExpression()
        if rType not in ('int', 'float'):
            failSem('невідповідність типів', (t0[0], t0[1], t0[2]))
        return rType
    elif t0[1] == '!':
        parseToken('!', 'logic_op')
        rType = parseUnaryExpression()
        if rType != 'bool':
            failSem('невідповідність типів', (t0[0], t0[1], t0[2]))
        return rType
    else:
        return parsePowerExpression()

def parsePowerExpression():
    indent = nextIndt()
    print(indent + 'parsePowerExpression():')
    lType = parsePrimaryExpression()
    if peek_tok(0)[1] == '^':
        t_op = peek_tok(0)
        parseToken('^', 'power_op')
        rType = parseUnaryExpression()
        lType = getTypeOp(lType, '^', rType)
        if lType == 'type_error':
            failSem('невідповідність типів', (t_op[0], t_op[1], t_op[2]))
    predIndt()
    return lType

def parsePrimaryExpression():
    indent = nextIndt()
    print(indent + 'parsePrimaryExpression():')
    t0 = peek_tok(0)
    res_type = 'type_error'

    if t0[2] == 'keyword' and t0[1] in ('int', 'float', 'bool', 'string'):
        res_type = parseCastExpression()
    elif t0[1] == 'c':
        res_type = parseArrayLiteral()
    elif t0[2] == 'id':
        attr = findName(t0[1], current_context)
        if not attr:
            failSem('неоголошена змінна', (t0[0], t0[1], t0[2]))
        
        t1 = peek_tok(1)
        if t1[1] == '(':
            res_type = parseFunctionCall()
        elif t1[1] == '[':
            res_type = parseArrayAccess()
            if attr[3] == 'undefined':
                failSem('неініціалізована змінна', (t0[0], t0[1], t0[2]))
        else:
            parseToken('', 'id')
            if attr[3] == 'undefined' and attr[1] != 'func':
                failSem('неініціалізована змінна', (t0[0], t0[1], t0[2]))
            res_type = attr[2]
    elif t0[1] == '(':
        parseToken('(', 'par_op')
        res_type = parseExpression()
        parseToken(')', 'par_op')
    elif t0[2] in ('int', 'float', 'string', 'bool'):
        parseToken(t0[1], t0[2])
        res_type = t0[2]
    else:
        failParse("очікувався первинний вираз", (t0[0], t0[1], t0[2], "ідентифікатор, літерал або '('"))
    
    predIndt()
    return res_type

def parseCastExpression():
    parseScalarType()
    parseToken('(', 'par_op')
    parseExpression()
    parseToken(')', 'par_op')
    return 'void'

def parseArrayLiteral():
    parseToken('c', 'array_ctor')
    parseToken('(', 'par_op')
    if peek_tok(0)[1] != ')':
        parseArgumentList()
    parseToken(')', 'par_op')
    return 'void'

def parseFunctionCall():
    t0 = peek_tok(0)
    attr = findName(t0[1], current_context)
    parseToken('', 'id')
    parseToken('(', 'par_op')
    if peek_tok(0)[1] != ')':
        parseArgumentList()
    parseToken(')', 'par_op')
    return attr[2] if attr else 'type_error'

def parseArrayAccess():
    t0 = peek_tok(0)
    attr = findName(t0[1], current_context)
    parseToken('', 'id')
    parseToken('[', 'brack_op')
    parseExpression()
    parseToken(']', 'brack_op')
    return attr[2].replace('[]', '') if attr else 'type_error'


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
