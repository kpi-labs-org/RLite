import sys

KEYWORDS = {
    'const', 'type', 'int', 'float', 'bool', 'string',
    'if', 'else', 'while', 'function', 'return',
    'read', 'print', 'TRUE', 'FALSE', 'c'
}

tokenTable = {
    ';': 'punct',
    ',': 'punct',
    '(': 'par_op',
    ')': 'par_op',
    '{': 'brace_op',
    '}': 'brace_op',
    '[': 'brack_op',
    ']': 'brack_op',
    '+': 'add_op',
    '-': 'add_op',
    '*': 'mult_op',
    '/': 'mult_op',
    '^': 'power_op',
    '&': 'logic_op',
    '|': 'logic_op',
    '<-': 'assign_op',
    '==': 'rel_op',
    '!=': 'rel_op',
    '<=': 'rel_op',
    '>=': 'rel_op',
    '<': 'rel_op',
    '>': 'rel_op',
    '!': 'logic_op'
}

initState = 0
# ДОДАНО 19 ДО МНОЖИНИ ЗАКЛЮЧНИХ СТАНІВ
F = {2, 5, 8, 13, 16, 18, 19, 22, 23, 25, 27, 29, 30, 101, 102, 103}
Fstar = {2, 5, 8, 13, 18}
Ferror = {101, 102, 103}

stf = {
    (0, 'ws'): 0,
    (0, 'nl'): 19,

    (0, '#'): 20,
    (20, 'nl'): 19,
    (20, 'other'): 20,

    (0, 'Letter'): 1,
    (1, 'Letter'): 1,
    (1, 'Digit'): 1,
    (1, 'other'): 2,

    (0, 'Digit'): 4,
    (4, 'Digit'): 4,
    (4, 'dot'): 6,
    (4, 'exp'): 9,
    (4, 'other'): 5,

    (0, 'dot'): 7,
    (7, 'Digit'): 6,
    (7, 'other'): 101,

    (6, 'Digit'): 6,
    (6, 'exp'): 9,
    (6, 'other'): 8,

    (9, 'sign'): 10,
    (9, 'Digit'): 11,
    (9, 'other'): 102,

    (10, 'Digit'): 11,
    (10, 'other'): 102,

    (11, 'Digit'): 11,
    (11, 'other'): 13,

    (0, 'quote'): 14,
    (14, 'quote'): 16,
    (14, 'escape'): 15,
    (14, 'nl'): 103,
    (14, 'other'): 14,
    (15, 'escaped_ch'): 14,
    (15, 'other'): 103,

    (0, '<'): 21,
    (21, '-'): 22,
    (21, '='): 23,
    (21, 'other'): 18,

    (0, '>'): 24,
    (24, '='): 25,
    (24, 'other'): 18,

    (0, '='): 26,
    (26, '='): 27,
    (26, 'other'): 101,

    (0, '!'): 28,
    (28, '='): 29,
    (28, 'other'): 18,

    (0, ';'): 30,
    (0, ','): 30,
    (0, '('): 30,
    (0, ')'): 30,
    (0, '{'): 30,
    (0, '}'): 30,
    (0, '['): 30,
    (0, ']'): 30,
    (0, '+'): 30,
    (0, '-'): 30,
    (0, '*'): 30,
    (0, '/'): 30,
    (0, '^'): 30,
    (0, '&'): 30,
    (0, '|'): 30,

    (0, 'other'): 101
}

sourceCode = ""
lenCode = 0
numLine = 1
numChar = -1
char = ""
state = initState
lexeme = ""

tableOfSymb = {}
tableOfId = {}
tableOfConst = {}


def init_lexer(code_text: str):
    global sourceCode, lenCode, numLine, numChar, char, state, lexeme
    global tableOfSymb, tableOfId, tableOfConst
    sourceCode = code_text
    lenCode = len(sourceCode)
    numLine = 1
    numChar = -1
    char = ""
    state = initState
    lexeme = ""
    tableOfSymb.clear()
    tableOfId.clear()
    tableOfConst.clear()


def classOfChar(ch: str) -> str:
    if state == 20:
        return 'nl' if ch == '\n' else 'other'

    if state in (14, 15):
        if state == 15:
            return 'escaped_ch' if ch in ('"', '\\', 'n', 'r', 't') else 'other'
        if ch == '"': return 'quote'
        if ch == '\\': return 'escape'
        if ch == '\n': return 'nl'
        return 'other'

    if ch in (' ', '\t', '\r', '\ufeff'):
        return 'ws'
    if ch == '\n':
        return 'nl'

    if ch.isalpha() or ch == '_':
        if state in (4, 6) and ch in ('e', 'E'):
            return 'exp'
        return 'Letter'

    if ch.isdigit():
        return 'Digit'

    if ch == '.':
        return 'dot'

    if ch in ('+', '-') and state in (9, 10):
        return 'sign'

    if ch == '"':
        return 'quote'

    if ch in ('<', '>', '=', '!', '+', '-', '*', '/', '^', '&', '|',
              '(', ')', '{', '}', '[', ']', ';', ',', '#'):
        return ch

    return 'other'


def nextChar() -> str:
    global numChar
    numChar += 1
    if numChar < lenCode:
        return sourceCode[numChar]
    return ""


def putCharBack():
    global numChar
    numChar -= 1


def nextState(curr_state: int, class_ch: str) -> int:
    try:
        return stf[(curr_state, class_ch)]
    except KeyError:
        return stf.get((curr_state, 'other'), 101)


def is_final(st: int) -> bool:
    return st in F


def indexId(id_lexeme: str) -> int:
    if id_lexeme not in tableOfId:
        tableOfId[id_lexeme] = len(tableOfId) + 1
    return tableOfId[id_lexeme]


def indexConst(const_lexeme: str, token_type: str) -> int:
    if const_lexeme not in tableOfConst:
        tableOfConst[const_lexeme] = (token_type, len(tableOfConst) + 1)
    return tableOfConst[const_lexeme][1]


def fail():
    if state == 101:
        print(f"Lexer: у рядку {numLine} неочікуваний або недопустимий символ '{char}'")
    elif state == 102:
        print(f"Lexer: у рядку {numLine} некоректний формат експоненти числа, знайдено '{char}'")
    elif state == 103:
        print(f"Lexer: у рядку {numLine} помилка в рядковому літералі (незакриті лапки)")
    sys.exit(1)


def processing():
    global state, lexeme, char, numLine, numChar

    if state == 19:
        numLine += 1
        state = initState
        lexeme = ''
        return

    if state in (22, 23, 25, 27, 29):
        token = tokenTable.get(lexeme, 'rel_op')
        tableOfSymb[len(tableOfSymb) + 1] = (numLine, lexeme, token, '')
        lexeme = ''
        state = initState
        return

    if state == 30:
        token = tokenTable.get(lexeme, 'punct')
        tableOfSymb[len(tableOfSymb) + 1] = (numLine, lexeme, token, '')
        lexeme = ''
        state = initState
        return

    if state == 16:
        idx = indexConst(lexeme, 'string')
        tableOfSymb[len(tableOfSymb) + 1] = (numLine, lexeme, 'string', idx)
        lexeme = ''
        state = initState
        return

    if state in Fstar:
        putCharBack()
        current_lexeme = lexeme[:-1]

        if state == 2:
            if current_lexeme in KEYWORDS:
                token = 'keyword' if current_lexeme not in ('TRUE', 'FALSE', 'c') else \
                        ('bool' if current_lexeme in ('TRUE', 'FALSE') else 'array_ctor')
                if token == 'bool':
                    idx = indexConst(current_lexeme, 'bool')
                    tableOfSymb[len(tableOfSymb) + 1] = (numLine, current_lexeme, token, idx)
                else:
                    tableOfSymb[len(tableOfSymb) + 1] = (numLine, current_lexeme, token, '')
            else:
                idx = indexId(current_lexeme)
                tableOfSymb[len(tableOfSymb) + 1] = (numLine, current_lexeme, 'id', idx)

        elif state == 5:
            idx = indexConst(current_lexeme, 'int')
            tableOfSymb[len(tableOfSymb) + 1] = (numLine, current_lexeme, 'int', idx)

        elif state in (8, 13):
            idx = indexConst(current_lexeme, 'float')
            tableOfSymb[len(tableOfSymb) + 1] = (numLine, current_lexeme, 'float', idx)

        elif state == 18:
            token = tokenTable.get(current_lexeme, 'rel_op')
            tableOfSymb[len(tableOfSymb) + 1] = (numLine, current_lexeme, token, '')

        lexeme = ''
        state = initState
        return

    if state in Ferror:
        fail()


def lex():
    global state, numLine, char, lexeme, numChar
    try:
        while numChar < lenCode - 1:
            char = nextChar()
            class_ch = classOfChar(char)
            state = nextState(state, class_ch)

            if state != initState and state != 20:
                lexeme += char

            if is_final(state):
                processing()

        if state != initState:
            if state == 20:
                state = initState
                lexeme = ''
            elif state in (1, 4, 6, 11, 21, 24, 28):
                lexeme += ' '
                state = nextState(state, 'other')
                if is_final(state):
                    processing()
                elif state in Ferror:
                    fail()
            elif state in (14, 15):
                state = 103
                fail()

        print("Lexer: Лексичний аналіз завершено успішно")
        return True

    except SystemExit as e:
        print(f"Lexer: Аварійне завершення програми з кодом {e}")
        return False


def print_results():
    print("\n" + "=" * 65)
    print("Таблиця символів програми (tableOfSymb):")
    print(f"{'№':<4} {'Рядок':<6} {'Лексема':<18} {'Токен':<14} {'Індекс'}")
    print("-" * 65)
    for n_rec, val in tableOfSymb.items():
        line, lxm, tok, idx = val
        idx_str = str(idx) if idx != '' else ''
        print(f"{n_rec:<4} {line:<6} {lxm:<18} {tok:<14} {idx_str}")

    print("\n" + "=" * 65)
    print("Таблиця ідентифікаторів (tableOfId):")
    print(f"{'Ідентифікатор':<25} {'Індекс'}")
    print("-" * 65)
    for ident, idx in tableOfId.items():
        print(f"{ident:<25} {idx}")

    print("\n" + "=" * 65)
    print("Таблиця констант (tableOfConst):")
    print(f"{'Константа':<20} {'Тип':<12} {'Індекс'}")
    print("-" * 65)
    for const_val, (tok, idx) in tableOfConst.items():
        print(f"{const_val:<20} {tok:<12} {idx}")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"Аналіз файлу: {filepath}\n")
            init_lexer(content)
            if lex():
                print_results()
        except FileNotFoundError:
            print(f"Файл {filepath} не знайдено.")
    else:
        print("Використання: python rlite_lexer.py <шлях_до_файлу_rlite>")