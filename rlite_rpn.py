import os
import sys
import rlite_lexer
import rlite_parser

class RPNGenerator:
    def __init__(self, root_name):
        self.modules = {}
        self.context_stack = [root_name]
        self.label_counter = 0
        self._init_module(root_name, 'univ', 'void', 0)

    def _init_module(self, mod_name, func_name, ret_type, n_params):
        self.modules[mod_name] = {
            'func_name': func_name,
            'ret_type': ret_type,
            'n_params': n_params,
            'vars': [],
            'var_set': set(),
            'globals': [],
            'global_set': set(),
            'funcs': {},
            'labels': {},
            'code': []
        }

    def cur(self):
        return self.modules[self.context_stack[-1]]

    def emit(self, lexeme, token):
        self.cur()['code'].append((lexeme, token))

    def code_len(self):
        return len(self.cur()['code'])

    def new_label(self):
        self.label_counter += 1
        return f"m{self.label_counter}"

    def place_label(self, lbl):
        mod = self.cur()
        mod['labels'][lbl] = len(mod['code'])
        self.emit(lbl, 'label')
        self.emit(':', 'colon')

    def _track_global(self, name, decl_scope):
        if len(self.context_stack) > 1 and decl_scope == 'univ':
            mod = self.cur()
            if name not in mod['var_set'] and name not in mod['global_set']:
                mod['global_set'].add(name)
                mod['globals'].append(name)

    def on_func_enter(self, id_val, type_val, prev_context):
        parent_mod = self.context_stack[-1]
        if prev_context == 'univ':
            func_rel = id_val
        else:
            func_rel = f"{parent_mod.split('$', 1)[1]}${id_val}"
        full_mod = f"{self.context_stack[0]}${func_rel}"
        self._init_module(full_mod, func_rel, type_val, 0)
        self.context_stack.append(full_mod)

    def on_func_params_done(self, id_val, prev_context, type_val, n_params):
        self.cur()['n_params'] = n_params
        parent_mod = self.context_stack[-2]
        func_rel = self.cur()['func_name']
        self.modules[parent_mod]['funcs'][func_rel] = (type_val, n_params)

    def on_func_exit(self, type_val):
        if type_val == 'void' and (not self.cur()['code'] or self.cur()['code'][-1] != ('RET', 'RET')):
            self.emit('RET', 'RET')
        self.context_stack.pop()

    def on_var_decl(self, id_val, type_val):
        mod = self.cur()
        if id_val not in mod['var_set']:
            mod['var_set'].add(id_val)
            mod['vars'].append((id_val, type_val))

    def on_assign_start(self, id_val, decl_scope):
        self._track_global(id_val, decl_scope)
        self.emit(id_val, 'l-val')

    def on_assign_end(self, lType, rType):
        if lType == 'float' and rType == 'int':
            self.emit('i2f', 'conv')
        self.emit('=', 'assign_op')

    def on_read_var(self, id_val, var_type, decl_scope):
        self._track_global(id_val, decl_scope)
        self.emit(id_val, 'l-val')
        self.emit('INP', 'inp_op')
        if var_type == 'int':
            self.emit('s2i', 'conv')
        elif var_type == 'float':
            self.emit('s2f', 'conv')
        elif var_type == 'bool':
            self.emit('s2i', 'conv')
            self.emit('i2b', 'conv')
        self.emit('=', 'assign_op')

    def on_print_item(self):
        self.emit('OUT', 'out_op')

    def on_if_cond(self):
        m1 = self.new_label()
        self.emit(m1, 'label')
        self.emit('JF', 'jf')
        return m1

    def on_if_else(self, m1):
        m2 = self.new_label()
        self.emit(m2, 'label')
        self.emit('JMP', 'jump')
        self.place_label(m1)
        return m2

    def on_if_end(self, lbl):
        self.place_label(lbl)

    def on_while_start(self):
        m1 = self.new_label()
        m2 = self.new_label()
        self.place_label(m1)
        return m1, m2

    def on_while_cond(self, m2):
        self.emit(m2, 'label')
        self.emit('JF', 'jf')

    def on_while_end(self, m1, m2):
        self.emit(m1, 'label')
        self.emit('JUMP', 'jump')
        self.place_label(m2)

    def on_return(self, rType):
        expected = self.cur()['ret_type']
        if expected == 'float' and rType == 'int':
            self.emit('i2f', 'conv')
        self.emit('RET', 'RET')

    def on_binop(self, op, lType, rType, left_pos):
        if op in ('|', '&'):
            self.emit('OR' if op == '|' else 'AND', 'bool_op')
        elif op == '^':
            if lType == 'int':
                self.cur()['code'].insert(left_pos, ('i2f', 'conv'))
            if rType == 'int':
                self.emit('i2f', 'conv')
            self.emit('^', 'pow_op')
        elif op in ('+', '-', '*', '/'):
            if lType == 'int' and rType == 'float':
                self.cur()['code'].insert(left_pos, ('i2f', 'conv'))
            elif lType == 'float' and rType == 'int':
                self.emit('i2f', 'conv')
            self.emit(op, 'math_op')
        else:
            if lType == 'int' and rType == 'float':
                self.cur()['code'].insert(left_pos, ('i2f', 'conv'))
            elif lType == 'float' and rType == 'int':
                self.emit('i2f', 'conv')
            self.emit(op, 'rel_op')

    def on_unop(self, op):
        if op == '-':
            self.emit('NEG', 'math_op')
        elif op == '!':
            self.emit('NOT', 'bool_op')

    def on_rval(self, name, decl_scope):
        self._track_global(name, decl_scope)
        self.emit(name, 'r-val')

    def on_literal(self, val, tok_type):
        self.emit(val, tok_type)

    def on_cast(self, src_type, target_type):
        conv_map = {
            ('int', 'float'): 'i2f',
            ('float', 'int'): 'f2i',
            ('int', 'string'): 'i2s',
            ('string', 'int'): 's2i',
            ('float', 'string'): 'f2s',
            ('string', 'float'): 's2f',
            ('bool', 'int'): 'b2i',
            ('int', 'bool'): 'i2b'
        }
        if (src_type, target_type) in conv_map:
            self.emit(conv_map[(src_type, target_type)], 'conv')

    def on_call(self, func_name, decl_scope, attr):
        call_name = func_name if decl_scope == 'univ' else f"{decl_scope}${func_name}"
        if call_name not in self.cur()['funcs'] and attr:
            self.cur()['funcs'][call_name] = (attr[2], attr[4])
        self.emit(call_name, 'CALL')

    def save(self, out_dir):
        os.makedirs(out_dir, exist_ok=True)
        for mod_name, mod in self.modules.items():
            filepath = os.path.join(out_dir, f"{mod_name}.postfix")
            lines = [
                ".target: Postfix Machine",
                ".version: 0.3",
                ""
            ]
            if mod['vars']:
                lines.append(".vars(")
                for v_name, v_type in mod['vars']:
                    lines.append(f"\t{v_name}\t{v_type}")
                lines.append(")")
                lines.append("")
            if mod['globals']:
                lines.append(".globVarList(")
                for g_name in mod['globals']:
                    lines.append(f"\t{g_name}")
                lines.append(")")
                lines.append("")
            if mod['funcs']:
                lines.append(".funcs(")
                for f_name, (f_ret, f_n) in mod['funcs'].items():
                    lines.append(f"\t{f_name}\t{f_ret}\t{f_n}")
                lines.append(")")
                lines.append("")
            if mod['labels']:
                lines.append(".labels(")
                for l_name, l_idx in mod['labels'].items():
                    lines.append(f"\t{l_name}\t{l_idx}")
                lines.append(")")
                lines.append("")
            lines.append(".code(")
            for lex, tok in mod['code']:
                if lex == 'RET' and tok == 'RET':
                    lines.append("\tRET")
                else:
                    lines.append(f"\t{lex}\t{tok}")
            lines.append(")")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("\n".join(lines) + "\n")
                
            print(f"\n=== Модуль: {filepath} ===")
            print(f"Таблиця міток: {mod['labels']}")
            print("Код ПОЛІЗ:")
            for idx, instr in enumerate(mod['code']):
                print(f"  {idx:3}: {instr}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        out_dir = sys.argv[2] if len(sys.argv) > 2 else 'out'
        base_name = os.path.splitext(os.path.basename(filepath))[0]
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"Трансляція файлу: {filepath}\n")
            rlite_lexer.init_lexer(content)
            if rlite_lexer.lex():
                rlite_parser.len_tableOfSymb = len(rlite_lexer.tableOfSymb)
                gen = RPNGenerator(base_name)
                rlite_parser.cg = gen
                if rlite_parser.parseProgram():
                    gen.save(out_dir)
        except FileNotFoundError:
            print(f"Файл {filepath} не знайдено.")
    else:
        print("Використання: python rlite_rpn.py <шлях_до_файлу_rlite> [вихідна_тека]")