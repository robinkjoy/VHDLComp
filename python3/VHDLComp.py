import vim
import sys
import re

def get_entity_name():
    vim.command('call inputsave()')
    vim.command("let user_input = input('Enter entity name: ')")
    vim.command('call inputrestore()')
    vim.command('redraw')
    return vim.eval('user_input')

def find_entity(ent):
    pattern = re.compile(r"^\s*entity\s+"+ent+"\s+is", flags=re.IGNORECASE)
    matches = [(b, li) for b in vim.buffers for li, l in enumerate(b) if pattern.match(l)]
    if len(matches) == 0:
        print('Entity '+ent+' not found', file=sys.stderr)
        return None
    elif len(matches) > 1:
        print('Multiple matches found for entity '+ent, file=sys.stderr)
        return None
    else:
        return matches[0]

def get_entity_dec(buf, line, ent):
    pattern = re.compile(r"^\s*end\s+(entity\s*)*"+ent+"\s*;", flags=re.IGNORECASE)
    lines = []
    for l in buf[line:]:
        lines.append(l)
        if pattern.match(l):
            return lines
    print('Check syntax of entity '+ent, file=sys.stderr)
    return None

def remove_comments(lines):
    p_all_comment = re.compile(r"^\s*--")
    p_comment = re.compile(r"\s*--.*$")
    lines = [l for l in lines if not p_all_comment.match(l)]
    lines = [re.sub(p_comment, '', l) for l in lines]
    return lines

def get_entity_lines():
    entity_name = get_entity_name()
    buf_line = find_entity(entity_name)
    if not buf_line:
        return
    (buf, line) = buf_line
    lines = get_entity_dec(buf, line, entity_name)
    if 'VHDLComp_remove_comments' in vim.vars and vim.vars['VHDLComp_remove_comments'] == 1:
        lines = remove_comments(lines)
    return lines

def get_indent(lines):
    pattern = re.compile(r"^(\s*)(port|generic)\s*\(*\s*$", flags=re.IGNORECASE)
    return next((pattern.search(l) for l in lines if pattern.search(l)), None)

def add_indent(lines):
    indent = get_indent(lines)
    if not indent:
        print('Empty entity?', file=sys.stderr)
        return None
    return [indent.group(1)+l for l in lines]

def convert_ent2comp(lines):
    lines[0] = re.sub(r"\bentity\b", "component", lines[0])
    lines[0] = re.sub(r"\s*\bis\b\s*$", "", lines[0])
    lines[-1] = re.sub(r"\bentity\b", "component", lines[-1])
    return lines

def vhdl_ent2comp():
    lines = get_entity_lines()
    if not lines:
        return
    lines = add_indent(lines)
    if not lines:
        return
    lines = convert_ent2comp(lines)
    vim.current.buffer.append(lines, vim.current.window.cursor[0]-1)

def convert_ent2sig(lines):
    p_all_comment = re.compile(r"^\s*--")
    p_port = re.compile(r"((?!--).)*:\s*(in|out|inout)\s+")
    p_generic_or_port = re.compile(r"((?!--).)*:")
    indent = get_indent(lines)
    if not indent:
        print('Empty entity?', file=sys.stderr)
        return None
    indent = indent.group(1)
    signals = [l for l in lines if p_all_comment.match(l) or p_generic_or_port.match(l)]
    def convert_line(l):
        if p_port.match(l):
            l = re.sub(r"^\s*", indent+'signal ', l, count=1)
            l = re.sub(r":\s*(in|out|inout)\s+", r": ", l, count=1)
            l = re.sub(r"^(((?!--).)*\bstd_logic\b\s*);*(.*)$", r"\1 := '0';\3", l, count=1)
            l = re.sub(r"^(((?!--).)*\))(\s*;)*(.*)$", r"\1 := (others => '0');\4", l, count=1)
        elif p_generic_or_port.match(l) and not p_port.match(l):
            l = re.sub(r"^\s*", indent+'constant ', l, count=1)
            l = re.sub(r"^(((?!\s*--)[^;])*);*(.*)", r"\1;\3", l, count=1)
        return l
    signals = [convert_line(l) for l in signals]
    return signals


def vhdl_ent2sig():
    lines = get_entity_lines()
    if not lines:
        return
    signals = convert_ent2sig(lines)
    vim.current.buffer.append(signals, vim.current.window.cursor[0]-1)

def convert_ent2inst(lines):
    indent = get_indent(lines)
    if not indent:
        print('Empty entity?', file=sys.stderr)
        return None
    inst = lines
    del inst[-1]
    inst = [re.sub(r"(\s*)(\S*)\s*:(((?!\s*--)[^;])*);*(.*)", r"\1\2 => \2, \5", l, count=1, flags=re.IGNORECASE) for l in inst]
    inst[0] = re.sub(r"^\s*entity\s+(\S*)\s*is.*", r"\1_inst : \1", inst[0], count=1, flags=re.IGNORECASE)
    inst = [re.sub(r"^(\s*)(generic|port)\s*\(", r"\1\2 map (", l, count=1, flags=re.IGNORECASE) for l in inst]
    # remove ,'s and ;'s
    p_all_comment = re.compile(r"^\s*--")
    p_strip_prev = re.compile(r"\s*(port map|\);)")
    strip = False
    for i, l in reversed(list(enumerate(inst))):
        if strip:
            inst[i] = re.sub(r"(((?!\s*--)[^,;])*)[,;](.*)", r"\1\3", l, count=1)
        if p_strip_prev.match(l):
            strip = True
        elif not p_all_comment.match(l):
            strip = False
    return [indent.group(1)+l for l in inst]

def vhdl_ent2inst():
    lines = get_entity_lines()
    if not lines:
        return
    inst = convert_ent2inst(lines)
    vim.current.buffer.append(inst, vim.current.window.cursor[0]-1)
