#!/usr/bin/python
#author: jobs
#email: yao050421103@gmail.com
import sys
import os.path
import datetime
import string
import json

CTYPE = 0
NAME = 1
ID = 2
KEY = 3 #append in runtime
TYPE = 4 #append in runtime
INIT = 5 #append in runtime

FILTER = '@null_string_place_holder'
merge = lambda l: string.join(filter(lambda item: FILTER != item, l), '\n')
json_filter = lambda f: (lambda f, l: os.path.splitext(f)[1] in l)(f, ['.json'])
is_array = lambda key: key.startswith('[') and key.endswith(']')
is_dict = lambda key: key.startswith('{') and key.endswith('}')
meta_type = lambda key: key[1:len(key) - 1]

def manual(): 
    print """
    usage:
        python rawbuf.py [option] filelist
            [option]
                -f: use file in filelist
                -p: use dir in filelist, will be parsed recursive
                
    sample:
        python rawbuf.py -f file1.json file2.json file3.json
        python rawbuf.py -p ./dir1/ ./dir2/ ./dir3/
        """

def get_file_list(cur_dir, path_filter):
    def __get(cur_dir, path_filter, file_list):
        for root, dirs, files in os.walk(cur_dir): 
            for f in files:
                if path_filter(f):
                    file_list.append(os.path.join(root, f))
    file_list = []
    __get(cur_dir, path_filter, file_list)
    return file_list

def get_files(file_filter, op, urls):
    if '-f' == op:
        return filter(file_filter, urls)
    elif '-p' == op:
        file_set = set()
        for url in urls:
            for item in get_file_list(url, file_filter):
                if not item in file_set:
                    file_set.add(item)
        return list(file_set)
    return []

def write_file(url, data):
    with open(url, 'w') as f:
        f.writelines(data)

def get_rb_types():
    return [
        { 'key': 'bool', 'ctype': 'bool', 'val': 'false' },
        { 'key': 'int8', 'ctype': 'int8_t', 'val': '0' },
        { 'key': 'uint8', 'ctype': 'uint8_t', 'val': '0' },
        { 'key': 'int16', 'ctype': 'int16_t', 'val': '0' },
        { 'key': 'uint16', 'ctype': 'uint16_t', 'val': '0' },
        { 'key': 'int32', 'ctype': 'int32_t', 'val': '0' },
        { 'key': 'uint32', 'ctype': 'uint32_t', 'val': '0' },
        { 'key': 'int64', 'ctype': 'int64_t', 'val': '0' },
        { 'key': 'uint64', 'ctype': 'uint64_t', 'val': '0' },
        { 'key': 'float', 'ctype': 'float', 'val': '0.0' },
        { 'key': 'double', 'ctype': 'double', 'val': '0.0' }
        ]
def get_rb_str_t():
    return { 'key': 'string', 'ctype': 'string', 'val': '""' }

def create_nested_buf(args, rc): 
    return merge([
    '    $buf = rb_nested_buf($rb_val, %s);' % args,
    '    if ($buf["size"] < 1)',
    '    {',
    '        return %s;' % rc,
    '    }'
    ])
def get_rb_methods():
    __sizeof = {
        'dec': lambda type: 'function rb_sizeof_%s($obj_val)' % type['key'],
        'imp': lambda type: '    return sizeof_%s;' % type['key']
        }
    __encode = {
        'dec': lambda type: 'function rb_encode_%s($obj_val, &$rb_val)' % type['key'],
        'imp': lambda type: merge([
            '    $size = sizeof_%s;' % type['key'],
            '    if (!rb_encode_check($rb_val, $size))',
            '    {',
            '        return false;',
            '    }',
            '    rb_set_%s($obj_val, $rb_val["pos"], $rb_val);' % type['key'],
            '    $rb_val["pos"] += $size;',
            '    return true;'
            ])
        }
    __decode = {
        'dec': lambda type: 'function rb_decode_%s(&$rb_val, $offset)' % type['key'],
        'imp': lambda type: merge([
            '    $size = sizeof_%s;' % type['key'],
            '    if (!rb_decode_check($rb_val, $offset, $size))',
            '    {',
            '        return array(null, false);',
            '    }',
            '    return array(rb_get_%s($rb_val, $rb_val["start"] + $offset), true);' % type['key']
            ])
        }
    return [__sizeof, __encode, __decode]

def get_array_frame():
    __eq = lambda base, key: merge([
        '    $ssize = count($src);',
        '    $dsize = count($dst);',
        '    if ($ssize != $dsize)',
        '    {',
        '        return false;',
        '    }',
        base['for'],
        '    {',
        base['eq'](key),
        '        {',
        '            return false;',
        '        }',
        '    }',
        '    return true;'
        ])
    __sizeof = lambda base, key: merge([
        '    $size = sizeof_rb_size + count($obj_val) * sizeof_rb_size;',
        base['for'],
        '    {',
        base['sizeof'](key),
        '    }',
        '    return $size;'
        ])
    __encode = lambda base, key: merge([
        create_nested_buf('0', 'false'),
        '    $count = count($obj_val);',
        '    if (!rb_set_array_count($count, $buf))',
        '    {',
        '        return false;',
        '    }',
        base['reset_idx'],
        base['for'],
        '    {',
        '        if (!rb_set_array_table_item($i, $buf["pos"] - $buf["start"], $buf))',
        '        {',
        '            return false;',
        '        }',
        base['encode'](key),
        '        {',
        '            return false;',
        '        }',
        base['incr_idx'],
        '    }',
        '    $rb_val["pos"] = $buf["pos"];',
        '    return true;'
        ])
    __decode = lambda base, key: merge([
        base['init'],
        create_nested_buf('$offset', 'array(null, false)'),
        '    $size = rb_get_array_count($buf);',
        '    if ($size < 1)',
        '    {',
        '        return array($obj_val, true);',
        '    }',
        '    $rc = true;',
        '    for ($i = 0; $i < $size; $i++)',
        '    {',
        '        list($off, $ok) = rb_get_array_table_item($i, $buf);',
        '        if (!$ok)',
        '        {',
        '            $rc = false;',
        '            break;',
        '        }',
        base['decode'](key),
        '        {',
        '            $rc = false;',
        '            break;',
        '        }',
        base['set'](key),
        '    }',
        '    return array($obj_val, $rc);'
        ])
    return {
        'eq': __eq,
        'sizeof': __sizeof,
        'encode': __encode,
        'decode': __decode
        }
def gen_array_imp(key, method): 
    return merge([
        method['dec'](key),
        '{',
        method['imp'](key),
        '}\n'
        ])

def get_array_methods(array_frame, is_scalar):
    __eq = {
        'dec': lambda key: 'function rb_eq_%s_array(&$src, &$dst)' % key,
        'imp': lambda key: array_frame['eq']({
            'type': 'array',
            'for': '    for ($i = 0; $i < $ssize; $i++)',
            'eq': lambda key: '        if ($src[$i] != $dst[$i])' if is_scalar else ('        if (!rb_eq_%s($src[$i], $dst[$i]))' % key)
            }, key)
        }
    __sizeof = {
        'dec': lambda key: 'function rb_sizeof_%s_array(&$obj_val)' % key,
        'imp': lambda key: array_frame['sizeof']({
            'for': '    foreach($obj_val as $i => $item)',
            'sizeof': lambda key: '        $size += rb_sizeof_%s($item);' % key
            }, key)
        }
    __encode = {
        'dec': lambda key: 'function rb_encode_%s_array(&$obj_val, &$rb_val)' % key,
        'imp': lambda key: array_frame['encode']({
            'reset_idx': FILTER,
            'incr_idx': FILTER,
            'for': '    foreach($obj_val as $i => $item)',
            'encode': lambda key: '        if (!rb_encode_%s($item, $buf))' % key
            }, key)
        }
    __decode = {
        'dec': lambda key: 'function rb_decode_%s_array(&$rb_val, $offset)' % key,
        'imp': lambda key: array_frame['decode']({
            'type': 'array',
            'init': '    $obj_val = array();',
            'decode': lambda key: merge([
                '        list($val, $ok) = rb_decode_%s($buf, $off);' % key,
                '        if (!ok)',
                ]),
            'set': lambda key: '        array_push($obj_val, $val);'
            }, key)
        }
    return [__eq, __sizeof, __encode, __decode]

def get_dict_methods(array_frame, is_scalar):
    __eq = {
        'dec': lambda key: 'function rb_eq_%s_dict(&$src, &$dst)' % key,
        'imp': lambda key: array_frame['eq']({
            'type': 'dict',
            'for': '    foreach($src as $key => $item)',
            'eq': lambda key: merge([
                '        if (!isset($dst[$key]))',
                '        {',
                '            return false;',
                '        }',
                '        if ($item != $dst[$key])' if is_scalar else ('        if (!rb_eq_%s($item, $dst[$key]))' % key)
                ])
            }, key)
        }
    __sizeof = {
        'dec': lambda key: 'function rb_sizeof_%s_dict(&$obj_val)' % key,
        'imp': lambda key: array_frame['sizeof']({
            'for': '    foreach($obj_val as $key => $item)',
            'sizeof': lambda key: merge([
                '        $size += rb_sizeof_string($key);',
                '        $size += rb_sizeof_%s($item);' % key
                ])
            }, key)
        }
    __encode = {
        'dec': lambda key: 'function rb_encode_%s_dict(&$obj_val, &$rb_val)' % key,
        'imp': lambda key: array_frame['encode']({
            'reset_idx': '    $i = 0;',
            'incr_idx': '        $i = $i + 1;',
            'for': '    foreach($obj_val as $key => $item)',
            'encode': lambda key: merge([
                '        if (!rb_encode_string($key, $buf))',
                '        {',
                '            return false;',
                '        }',
                '        if (!rb_encode_%s($item, $buf))' % key
                ])
            }, key)
        }
    __decode = {
        'dec': lambda key: 'function rb_decode_%s_dict(&$rb_val, $offset)' % key,
        'imp': lambda key: array_frame['decode']({
            'type': 'dict',
            'init': '    $obj_val = array();',
            'decode': lambda key: merge([
                '        list($key, $ok) = rb_decode_string($buf, $off);',
                '        if (!$ok)',
                '        {',
                '            $rc = false;',
                '            break;',
                '        }',
                '        $delta = rb_sizeof_string($key);',
                '        list($val, $ok) = rb_decode_%s($buf, $off + $delta);' % key,
                '        if (!$ok)'
                ]),
            'set': lambda key: '        $obj_val[$key] = $val;'
            }, key)
        }
    return [__eq, __sizeof, __encode, __decode]

def get_header():
    return merge([
        '////////////////////////////////////////////////////////////////////////////////',
        '// NOTE : Generated by rawbuf. It is NOT supposed to modify this file.',
        '////////////////////////////////////////////////////////////////////////////////'
        ])

def get_object_methods(scalars):
    def is_scalar(scalars, member):
        for scalar in scalars:
            if member[CTYPE] == scalar['ctype']:
                return True
        return False
    __create = {
        'dec': lambda key: 'function rb_create_%s()' % key.lower(),
        'imp': lambda key, members: merge([
            '    return array(',
            merge([merge([
                '        "%s" => %s,' % (member[NAME], member[INIT]),
                '        "id_%s" => %s,' % (member[NAME], member[ID]),
                '        "skip_%s" => false,' % member[NAME],
                '        "rb_has_%s" => false%s' % (member[NAME], ',' if (members.index(member) < len(members) - 1) else '')
                ]) for member in members]),
            '    );'
            ])
        }
    __eq_field = lambda scalars, member: merge([
        '    if ($src["%s"] != $dst["%s"])' % (member[NAME], member[NAME]),
        '    {',
        '        return false;',
        '    }'
        ]) if is_scalar(scalars, member) else merge([
        '    if (!rb_eq_%s($src["%s"], $dst["%s"]))' % (member[TYPE].lower(), member[NAME], member[NAME]),
        '    {',
        '        return false;',
        '    }'
        ])
    __eq = {
        'dec': lambda key: 'function rb_eq_%s(&$src, &$dst)' % key.lower(),
        'imp': lambda key, members: merge([
            merge([__eq_field(scalars, member) for member in members]),
            '    return true;'
            ])
        }
    __rb_fields = {
        'dec': lambda key: 'function rb_fields_%s(&$obj_val)' % key.lower(),
        'imp': lambda key, members: merge([
            '    $fields = 0;',
            merge([merge([
                '    if (!$obj_val["skip_%s"])' % member[NAME],
                '    {',
                '        $fields = $fields + 1;',
                '    }'
                ]) for member in members]),
            '    return $fields;'
            ])
        }
    __sizeof = {
        'dec': lambda key: 'function rb_sizeof_%s(&$obj_val)' % key.lower(),
        'imp': lambda key, members: merge([
            '    $fields = 0;',
            '    $size = 0;',
            merge([merge([
                '    if (!$obj_val["skip_%s"])' % member[NAME],
                '    {',
                '        $size += rb_sizeof_%s($obj_val["%s"]);' % (member[TYPE].lower(), member[NAME]),
                '        $fields = $fields + 1;',
                '    }'
                ]) for member in members]),
            '    $size += rb_seek_field_table_item($fields);',
            '    $size += sizeof_rb_buf_end;',
            '    return $size;'
            ])
        }
    __encode = {
        'dec': lambda key: 'function rb_encode_%s(&$obj_val, &$rb_val)' % key.lower(),
        'imp': lambda key, members: merge([
            create_nested_buf('0', 'false'),
            merge([
                '    $fields = rb_fields_%s($obj_val);' % key.lower(),
                '    $index = 0;',
                '    if (!rb_set_field_count($fields, $buf))',
                '    {',
                '        return false;',
                '    }',
                merge([merge([
                    '    if (!$obj_val["skip_%s"])' % member[NAME],
                    '    {',
                    '        if (!rb_set_field_table_item($index, $obj_val["id_%s"], $buf["pos"] - $buf["start"], $buf))' % member[NAME],
                    '        {',
                    '            return false;',
                    '        }',
                    '        if (!rb_encode_%s($obj_val["%s"], $buf))' % (member[TYPE].lower(), member[NAME]),
                    '        {',
                    '            return false;',
                    '        }',
                    '        $index = $index + 1;',
                    '    }'
                    ]) for member in members]) + '\n',
                '    if (!rb_set_buf_size($buf["pos"] - $buf["start"] + sizeof_rb_buf_end, $buf))',
                '    {',
                '        return false;',
                '    }',
                '    if (!rb_encode_end($fields, $buf))',
                '    {',
                '        return false;',
                '    }',
                '    $rb_val["pos"] = $buf["pos"];\n',
                '    return true;'
                ])
            ])
        }
    __decode = {
        'dec': lambda key: 'function rb_decode_%s(&$rb_val, $offset)' % key.lower(),
        'private_imp': lambda key, members: merge([
            'function __decode_%s($id, $offset, &$rb_val, &$obj_val)' % key.lower(),
            '{',
            merge([merge([
                '    if ($id == $obj_val["id_%s"])' % member[NAME],
                '    {',
                '        list($obj_val["%s"], $rc) = rb_decode_%s($rb_val, $offset);' % (member[NAME], member[TYPE].lower()),
                '        if ($rc) ',
                '        {',
                '            $obj_val["rb_has_%s"] = true;' % member[NAME],
                '        }',
                '        return $rc;',
                '    }'
                ]) for member in members]),
            '    return true;',
            '}\n'
            ]),
        'imp': lambda key, members: merge([
            create_nested_buf('$offset', 'array(null, false)'),
            '    list($size, $fields) = rb_get_field_table_head($buf);',
            '    if ($fields < 1 || !rb_check_code($buf, $size, $fields))',
            '    {',
            '        return array(null, false);',
            '    }',
            '    $obj_val = rb_create_%s();' % key.lower(),
            '    for ($i = 0; $i < $fields; $i++)',
            '    {',
            '        list($id, $off, $rc) = rb_get_field_table_item($i, $buf);',
            '        if (!$rc)',
            '        {',
            '            return array(null, false);',
            '        }',
            '        if ($off >= $size)',
            '        {',
            '            return array(null, false);',
            '        }',
            '        if ($off > 0 && !__decode_%s($id, $off, $buf, $obj_val))' % key.lower(),
            '        {',
            '            return array(null, false);',
            '        }',
            '    }',
            '    return array($obj_val, true);'
            ])
        }
    __dump = {
        'dec': lambda key: 'function rb_dump_%s(&$obj_val, $path)' % key.lower(),
        'imp': lambda key, members: merge([
            '    $size = rb_sizeof_%s($obj_val);' % key.lower(),
            '    if ($size < 1)',
            '    {',
            '        return false;',
            '    }',
            '    return rb_dump_buf(rb_encode_%s, $obj_val, $size, $path);' % key.lower(),
            ])
        }
    __load = {
        'dec': lambda key: 'function rb_load_%s($path)' % key.lower(),
        'imp': lambda key, members: '    return rb_load_buf($path, rb_decode_%s);' % key.lower()
        }
    return [__create, __eq, __rb_fields, __sizeof, __encode, __decode, __dump, __load]

def gen_from_schema(path, obj, scalars, object_methods, array_methods, dict_methods):
    gen_array = lambda struct: 'gen_array' in struct and struct['gen_array']
    def __check(structs):
        for struct in structs:
            ctype = struct['type']
            if not ctype.endswith('_t'):
                print '"%s" is not end with "_t"' % ctype
                return False
            ids = set()
            for member in struct['members']:
                if len(member) > (KEY) or len(member) < (ID):
                    print 'invalid members: "%s" in struct "%s"' % (str(member), ctype)
                    return False
                if len(member) < (ID + 1):
                    continue
                id = member[ID]
                if int(id) > 255:
                    print 'invalid id (should be: [0, 255]): "%s" in struct "%s"' % (str(member), ctype)
                    return False
                if id in ids:
                    print '"%s" duplicated in "%s"' % (str(id), ctype)
                    return False
                else:
                    ids.add(id)
        return True
    def __get_key(scalars, ctype):
        for type in scalars:
            if ctype == type['ctype']:
                return type['key']
        if ctype.endswith('_t'):
            return ctype[:(len(ctype) - len('_t'))]
        return ctype
    def __get_type(scalars, key):
        if is_array(key):
            meta = meta_type(key)
            if 'string' == meta:
                return 'string_array'
            return '%s_array' % __get_key(scalars, meta)
        if is_dict(key):
            meta = meta_type(key)
            if 'string' == meta:
                return 'string_dict'
            return '%s_dict' % __get_key(scalars, meta)
        if 'string' == key:
            return 'string'
        return __get_key(scalars, key)
    def __get_init(scalars, member):
        if is_array(member[CTYPE]) or is_dict(member[CTYPE]):
            return 'array()'
        else:
            for scalar in scalars:
                if scalar['ctype'] == member[CTYPE]:
                    return scalar['val']
        return 'rb_create_%s()' % member[TYPE]
    def __update_object(obj, scalars):
        def __update_ids(members):
            ids = [member[ID] for member in filter(lambda member: len(member) > ID, members)]
            default_ids = [str(members.index(member)) for member in members]
            for id in default_ids:
                if id in ids:
                    default_ids.remove(id)
            for member in members:
                if not len(member) > ID:
                    id = default_ids[0]
                    member.append(id)
                    default_ids.remove(id)
        size = len(obj['structs'])
        for struct in obj['structs']:
            if size - 1 == obj['structs'].index(struct):
                struct['gen_array'] = False
            else:
                struct['gen_array'] = True
            struct['key'] = __get_key(scalars, struct['type'])
            struct['ctype'] = struct['type']
            __update_ids(struct['members'])
            for member in struct['members']:
                member.append(__get_key(scalars, member[CTYPE]))
                member.append(__get_type(scalars, member[CTYPE]))
                member.append(__get_init(scalars, member))
    def __gen_implement(path, obj, scalars, object_methods, array_methods, dict_methods):
        def __gen_struct(struct, scalars, object_methods, array_methods, dict_methods):
            __gen_imp = lambda key, members, method: merge([
                method['private_imp'](key, members) if 'private_imp' in method else FILTER,
                method['dec'](key),
                '{',
                method['imp'](key, members),
                '}\n'
                ])
            __gen_object_implement = lambda key, members, methods: merge([__gen_imp(key, members, method) for method in methods])
            __gen_array_imp = lambda key, methods: merge([
                gen_array_imp(key, method) for method in methods
                ])
            __gen_array_implement = lambda key, array_methods, dict_methods: merge([
                __gen_array_imp(key, array_methods),
                __gen_array_imp(key, dict_methods)
                ])
            return merge([
                __gen_object_implement(struct['key'], struct['members'], object_methods),
                __gen_array_implement(struct['key'], array_methods, dict_methods) if gen_array(struct) else FILTER
                ])
        write_file(path + ".php", merge([
            '<?php',
            get_header(),
            'require_once "rawbuf.php";\n',
            merge([__gen_struct(struct, scalars, object_methods, array_methods, dict_methods) for struct in obj['structs']]),
            '?>'
            ]))
    if not __check(obj['structs']):
        return False
    __update_object(obj, scalars)
    __gen_implement(path, obj, scalars, object_methods, array_methods, dict_methods)
    return True

def gen_rawbuf(path, types, str_t, methods, array_methods, dict_methods):
    __gen_imp = lambda type, method: merge([
        method['dec'](type),
        '{',
        method['imp'](type),
        '}\n'   
        ])
    scalars = list(types)
    scalars.append(str_t)
    write_file(path + ".php", merge([
        '<?php',
        get_header(),
        'require_once "rawbuf_utils.php";\n',
        merge([merge([__gen_imp(type, method) for type in types]) for method in methods]),
        merge([merge([gen_array_imp(type['key'], method) for method in array_methods]) for type in scalars]),
        merge([merge([gen_array_imp(type['key'], method) for method in dict_methods]) for type in scalars]),
        '?>'
        ]))
    return True
def gen(file_list, types, str_t, array_methods, dict_methods):
    scalars = list(types)
    scalars.append(str_t)
    object_methods = get_object_methods(scalars)
    for path_item in file_list:
        with open(path_item, 'r') as f:
            obj = json.load(f)
            gen_from_schema(
                path_item[:path_item.rfind('.')], 
                obj, 
                scalars,
                object_methods,
                array_methods,
                dict_methods)
    return True

def parse_shell(argv):
    def __get_path(argv):
        __path = '.' if 2 != len(argv) else argv[1]
        return os.path.join(os.path.abspath(__path), 'rawbuf')
    size = len(argv)
    array_frame = get_array_frame()
    if 1 == size or 2 == size:
        return gen_rawbuf(
            __get_path(argv), 
            get_rb_types(), 
            get_rb_str_t(), 
            get_rb_methods(), 
            get_array_methods(array_frame, True),
            get_dict_methods(array_frame, True))
    op = argv[1]
    file_list = get_files(json_filter, op, argv[2:])
    return gen(
        file_list, 
        get_rb_types(), 
        get_rb_str_t(), 
        get_array_methods(array_frame, False),
        get_dict_methods(array_frame, False)
        ) if len(file_list) > 0 else False

if __name__ == "__main__":
    if not parse_shell(sys.argv):
        manual()