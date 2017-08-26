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

FILTER = '@null_string_place_holder'
merge = lambda l: string.join(filter(lambda item: FILTER != item, l), '\n')
json_filter = lambda f: (lambda f, l: os.path.splitext(f)[1] in l)(f, ['.json'])

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
    os.system('gofmt -w %s' % url)

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
        { 'key': 'float32', 'ctype': 'float', 'val': '0.0' },
        { 'key': 'float64', 'ctype': 'double', 'val': '0.0' }
        ]
def get_rb_str_t():
    return { 'key': 'string', 'ctype': 'string' }

def create_nested_buf(args): 
    return merge([
    '    buf := Rb_nested_buf(rb_val, %s)' % args,
    '    if buf.Size < 1 {',
    '        return false',
    '    }'
    ])
def get_rb_methods():
    __pre_check_str = merge([
        '    if nil == src || nil == dst {',
        '        return false',
        '    }',
        ])
    __init = {
        'dec': lambda type: 'func Rb_init_%s(obj_val *%s)' % (type['key'], type['key']),
        'imp': lambda type: merge([
            '    if nil != obj_val {',
            '        *obj_val = %s' % type['val'],
            '    }',
            ])
        }
    __set = {
        'dec': lambda type: 'func Rb_set_%s(src *%s, dst *%s) bool' % (type['key'], type['key'], type['key']),
        'imp': lambda type: merge([
            __pre_check_str,
            '    *dst = *src',
            '    return true'
            ])
        }
    __eq = {
        'dec': lambda type: 'func Rb_eq_%s(src *%s , dst *%s) bool' % (type['key'], type['key'], type['key']),
        'imp': lambda type: merge([
            __pre_check_str,
            '    return *src == *dst'
            ])
        }
    __sizeof = {
        'dec': lambda type: 'func Rb_sizeof_%s(obj_val *%s) Rb_size_t' % (type['key'], type['key']),
        'imp': lambda type: '    return Sizeof_%s' % type['key']
        }
    __encode = {
        'dec': lambda type: 'func Rb_encode_%s(obj_val *%s, rb_val *Rb_buf_t) bool' % (type['key'], type['key']),
        'imp': lambda type: merge([
            '    size := Sizeof_%s' % type['key'],
            '    if nil == obj_val || !Rb_encode_check(rb_val, size) {',
            '        return false',
            '    }',
            '    Set_%s(*obj_val, Rb_get_buf_from_pos(rb_val))' % type['key'],
            '    rb_val.Pos += size',
            '    return true'
            ])
        }
    __decode = {
        'dec': lambda type: 'func Rb_decode_%s(rb_val *Rb_buf_t, offset Rb_offset_t, obj_val *%s) bool' % (type['key'], type['key']),
        'imp': lambda type: merge([
            '    size := Sizeof_%s' % type['key'],
            '    if nil == obj_val || !Rb_decode_check(rb_val, offset, size) {',
            '        return false',
            '    }',
            '    *obj_val = Get_%s(Rb_get_buf_from_offset(rb_val, rb_val.Start+Rb_size_t(offset)))' % type['key'],
            '    return true'
            ])
        }
    return [__init, __set, __eq, __sizeof, __encode, __decode]

def get_array_frame():
    __init = lambda base, key, ctype: merge([
        '    if nil == obj_val {',
        '        return',
        '    }',
        base['for'],
        base['init'](key, ctype),
        '    }'
        ])
    __set = lambda base, key, ctype: merge([
        '    if nil == src || nil == dst {',
        '        return false',
        '    }',
        '    ssize := len(*src)',
        '    if ssize < 1 {',
        '        return true',
        '    }',
        '    *dst = %s_%s_t{}' % (key.capitalize(), base['type']),
        base['for'],
        base['set'](key, ctype),
        '    }',
        '    return true'
        ])
    __eq = lambda base, key, ctype: merge([
        '    if nil == src || nil == dst {',
        '        return false',
        '    }',
        '    ssize := len(*src)',
        '    dsize := len(*dst)',
        '    if ssize != dsize {',
        '        return false',
        '    }',
        '    for key, val:= range *src {',
        base['eq'](key, ctype),
        '            return false',
        '        }',
        '    }',
        '    return true'
        ])
    __sizeof = lambda base, key, ctype: merge([
        '    size := Sizeof_rb_size + Rb_size_t(len(*obj_val)) * Sizeof_rb_size',
        base['for'],
        base['sizeof'](key, ctype),
        '    }',
        '    return size'
        ])
    __encode = lambda base, key, ctype: merge([
        '    if nil == obj_val {',
        '        return false',
        '    }',
        create_nested_buf('0'),
        '    count := Rb_size_t(len(*obj_val))',
        '    if !Rb_set_array_count(count, buf) {',
        '        return false',
        '    }',
        '    i := Rb_size_t(0)',
        base['for'],
        '        if !Rb_set_array_table_item(i, Rb_offset_t(buf.Pos - buf.Start), buf) {',
        '            return false',
        '        }',
        base['encode'](key, ctype),
        '            return false',
        '        }',
        '        i++',
        '    }',
        '    rb_val.Pos = buf.Pos',
        '    return true'
        ])
    __decode = lambda base, key, ctype: merge([
        '    if nil == obj_val {',
        '        return false',
        '    }',
        create_nested_buf('offset'),
        '    size := Rb_get_array_count(buf)',
        '    if size < 1 {',
        '        return true',
        '    }',
        '',
        '    *obj_val = %s_%s_t{}' % (key.capitalize(), base['type']),
        '',
        '    rc := true',
        '    ok := true',
        '    off := Rb_offset_t(0)',
        '    for i := Rb_size_t(0); i < size; i++ {',
        '        if ok, off = Rb_get_array_table_item(i, buf); !ok {',
        '            rc = false',
        '            break',
        '        }',
        base['init'](key, ctype),
        base['decode'](key, ctype),
        '            rc = false',
        '            break',
        '        }',
        base['set'](key, ctype),
        '    }',
        '    return rc'
        ])
    return {
        'init': __init,
        'set': __set,
        'eq': __eq,
        'sizeof': __sizeof,
        'encode': __encode,
        'decode': __decode
        }
def gen_array_def(key, ctype, is_scalar):
    return 'type %s_array_t []%s' % (key.capitalize(), key if is_scalar else ('(*%s)' % ctype.capitalize()))
def gen_array_imp(key, ctype, method, is_scalar): 
    return merge([
        method['dec'](key, ctype) + ' {',
        method['imp'](key, key if is_scalar else ctype),
        '}',
        ''
        ])
def gen_array_init(key, ctype, is_scalar):
    return merge([
        '        val := new(%s)' % (ctype if is_scalar else ctype.capitalize()),
        '        Rb_init_%s(val)' % (ctype if is_scalar else key)
        ])

def get_array_methods(array_frame, is_scalar, ref):
    __init = {
        'dec': lambda key, ctype: 'func Rb_init_%s_array(obj_val *%s_array_t)' % (key, key.capitalize()),
        'imp': lambda key, ctype: array_frame['init']({
            'init': lambda key, ctype: '        Rb_init_%s(%sval)' % (key, ref),
            'for': '    for _, val:= range *obj_val {'
            }, key, ctype)
        }
    __set = {
        'dec': lambda key, ctype: 'func Rb_set_%s_array(src *%s_array_t, dst *%s_array_t) bool' % (key, key.capitalize(), key.capitalize()),
        'imp': lambda key, ctype: array_frame['set']({
            'type': 'array',
            'for': '    for _, val:= range *src {',
            'set': lambda key, ctype: '        *dst = append(*dst, val)'
            }, key, ctype)
        }
    __eq = {
        'dec': lambda key, ctype: 'func Rb_eq_%s_array(src *%s_array_t, dst *%s_array_t) bool' % (key, key.capitalize(), key.capitalize()),
        'imp': lambda key, ctype: array_frame['eq']({
            'type': 'array',
            'eq': lambda key, ctype: '        if !Rb_eq_%s(%sval, %s(*dst)[key]) {' % (key, ref, ref)
            }, key, ctype)
        }
    __sizeof = {
        'dec': lambda key, ctype: 'func Rb_sizeof_%s_array(obj_val *%s_array_t) Rb_size_t' % (key, key.capitalize()),
        'imp': lambda key, ctype: array_frame['sizeof']({
            'for': '    for _, val:= range *obj_val {',
            'sizeof': lambda key, ctype: '        size += Rb_sizeof_%s(%sval)' % (key, ref)
            }, key, ctype)
        }
    __encode = {
        'dec': lambda key, ctype: 'func Rb_encode_%s_array(obj_val *%s_array_t, rb_val *Rb_buf_t) bool' % (key, key.capitalize()),
        'imp': lambda key, ctype: array_frame['encode']({
            'for': '    for _, val:= range *obj_val {',
            'encode': lambda key, ctype: '        if !Rb_encode_%s(%sval, buf) {' % (key, ref)
            }, key, ctype)
        }
    __decode = {
        'dec': lambda key, ctype: 'func Rb_decode_%s_array(rb_val *Rb_buf_t, offset Rb_offset_t, obj_val *%s_array_t) bool' % (key, key.capitalize()),
        'imp': lambda key, ctype: array_frame['decode']({
            'type': 'array',
            'init': lambda key, ctype: gen_array_init(key, ctype, is_scalar),
            'decode': lambda key, ctype: '        if !Rb_decode_%s(buf, off, val) {' % key,
            'set': lambda key, ctype: '        *obj_val = append(*obj_val, %sval)' % ('*' if is_scalar else '')
            }, key, ctype)
        }
    return [__init, __set, __eq, __sizeof, __encode, __decode]

def gen_dict_def(key, ctype, is_scalar):
    return 'type %s_dict_t map[string]%s' % (key.capitalize(), key if is_scalar else ('(*%s)' % ctype.capitalize()))
def get_dict_methods(array_frame, is_scalar, ref):
    __init = {
        'dec': lambda key, ctype: 'func Rb_init_%s_dict(obj_val *%s_dict_t)' % (key, key.capitalize()),
        'imp': lambda key, ctype: array_frame['init']({
            'init': lambda key, ctype: merge([
                '        Rb_init_string(&key)',
                '        Rb_init_%s(%sval)' % (key, ref)
                ]),
            'for': '    for key, val:= range *obj_val {'
            }, key, ctype)
        }
    __set = {
        'dec': lambda key, ctype: 'func Rb_set_%s_dict(src *%s_dict_t, dst *%s_dict_t) bool' % (key, key.capitalize(), key.capitalize()),
        'imp': lambda key, ctype: array_frame['set']({
            'type': 'dict',
            'for': '    for key, val:= range *src {',
            'set': lambda key, ctype: '        (*dst)[key] = val'
            }, key, ctype)
        }
    __eq = {
        'dec': lambda key, ctype: 'func Rb_eq_%s_dict(src *%s_dict_t, dst *%s_dict_t) bool' % (key, key.capitalize(), key.capitalize()),
        'imp': lambda key, ctype: array_frame['eq']({
            'type': 'dict',
            'eq': lambda key, ctype: merge([
                '        tmpval, ok := (*dst)[key]',
                '        if !ok {',
                '            return false',
                '        }',
                '        if !Rb_eq_%s(%sval, %stmpval) {' % (key, ref, ref)
                ])
            }, key, ctype)
        }
    __sizeof = {
        'dec': lambda key, ctype: 'func Rb_sizeof_%s_dict(obj_val *%s_dict_t) Rb_size_t' % (key, key.capitalize()),
        'imp': lambda key, ctype: array_frame['sizeof']({
            'for': '    for key, val:= range *obj_val {',
            'sizeof': lambda key, ctype: merge([
                '        size += Rb_sizeof_string(&key)',
                '        size += Rb_sizeof_%s(%sval)' % (key, ref)
                ])
            }, key, ctype)
        }
    __encode = {
        'dec': lambda key, ctype: 'func Rb_encode_%s_dict(obj_val *%s_dict_t, rb_val *Rb_buf_t) bool' % (key, key.capitalize()),
        'imp': lambda key, ctype: array_frame['encode']({
            'for': '    for key, val:= range *obj_val {',
            'encode': lambda key, ctype: merge([
                '        if !Rb_encode_string(&key, buf) {',
                '            return false',
                '        }',
                '        if !Rb_encode_%s(%sval, buf) {' % (key, ref)
                ])
            }, key, ctype)
        }
    __decode = {
        'dec': lambda key, ctype: 'func Rb_decode_%s_dict(rb_val *Rb_buf_t, offset Rb_offset_t, obj_val *%s_dict_t) bool' % (key, key.capitalize()),
        'imp': lambda key, ctype: array_frame['decode']({
            'type': 'dict',
            'init': lambda key, ctype: gen_array_init(key, ctype, is_scalar),
            'decode': lambda key, ctype: merge([
                '        var key string',
                '        if !Rb_decode_string(buf, off, &key) {',
                '            rc = false',
                '            break',
                '        }',
                '        delta := Rb_offset_t(Rb_sizeof_string(&key))',
                '        if !Rb_decode_%s(buf, off + delta, val) {' % key
                ]),
            'set': lambda key, ctype: '        (*obj_val)[key] = %sval' % ('*' if is_scalar else '')
            }, key, ctype)
        }
    return [__init, __set, __eq, __sizeof, __encode, __decode]

def get_header():
    return merge([
        '////////////////////////////////////////////////////////////////////////////////',
        '// NOTE : Generated by rawbuf. It is NOT supposed to modify this file.',
        '////////////////////////////////////////////////////////////////////////////////'
        ])

def gen_rawbuf(path, types, str_t, methods, array_methods, dict_methods):
    __gen_imp = lambda type, method: merge([
        method['dec'](type) + ' {',
        method['imp'](type),
        '}',
        ''
        ])
    full_types = list(types)
    full_types.append(str_t)
    write_file(path + ".go", merge([
        get_header(),
        'package rawbuf',
        '',
        merge([merge([__gen_imp(type, method) for type in types]) for method in methods]),
        merge([merge([gen_array_def(type['key'], type['ctype'], True), '']) for type in full_types]),
        merge([merge([gen_array_imp(type['key'], type['ctype'], method, True) for method in array_methods]) for type in full_types]),
        merge([merge([gen_dict_def(type['key'], type['ctype'], True), '']) for type in full_types]),
        merge([merge([gen_array_imp(type['key'], type['ctype'], method, True) for method in dict_methods]) for type in full_types]),
        ''
        ]))
    return True

def get_object_methods():
    __pre_check_pair_str = merge([
        '    if nil == src || nil == dst {',
        '        return false',
        '    }',
        ])
    __init = {
        'dec': lambda key, ctype: 'func Rb_init_%s(obj_val *%s)' % (key.lower(), ctype.capitalize()),
        'imp': lambda key, ctype, members: merge([
            '    if nil == obj_val {',
            '        return',
            '    }',
            merge([merge([
                '',
                '    Rb_init_%s(&obj_val.%s)' % (member[KEY].lower(), member[NAME].capitalize()),
                '    obj_val.Id_%s = %s' % (member[NAME], member[ID]),
                '    obj_val.Skip_%s = false' % member[NAME],
                '    obj_val.Rb_has_%s = false' % member[NAME]
                ]) for member in members])
            ])
        }
    __set = {
        'dec': lambda key, ctype: 'func Rb_set_%s(src *%s, dst *%s) bool' % (key.lower(), ctype.capitalize(), ctype.capitalize()),
        'imp': lambda key, ctype, members: merge([
            __pre_check_pair_str,
            merge(['    dst.Id_%s = src.Id_%s' % (member[NAME], member[NAME]) for member in members]),
            merge(['    if !Rb_set_%s(&src.%s, &dst.%s) { return false }' % (
                member[KEY].lower(), member[NAME].capitalize(), member[NAME].capitalize()) for member in members]),
            '    return true'
            ])
        }
    __eq = {
        'dec': lambda key, ctype: 'func Rb_eq_%s(src *%s, dst *%s) bool' % (key.lower(), ctype.capitalize(), ctype.capitalize()),
        'imp': lambda key, ctype, members: merge([
            __pre_check_pair_str,
            merge(['    if !Rb_eq_%s(&src.%s, &dst.%s) { return false }' % (
                member[KEY].lower(), member[NAME].capitalize(), member[NAME].capitalize()) for member in members]),
            '    return true'
            ])
        }
    __rb_fields = {
        'dec': lambda key, ctype: 'func Rb_fields_%s(obj_val *%s) Rb_field_size_t' % (key.lower(), ctype.capitalize()),
        'imp': lambda key, ctype, members: merge([
            '    fields := Rb_field_size_t(0)',
            merge(['    if !obj_val.Skip_%s { fields++ }' % member[NAME] for member in members]),
            '    return fields'
            ])
        }
    __sizeof = {
        'dec': lambda key, ctype: 'func Rb_sizeof_%s(obj_val *%s) Rb_size_t' % (key.lower(), ctype.capitalize()),
        'imp': lambda key, ctype, members: merge([
            '    fields := Rb_field_size_t(0)',
            '    size := Rb_size_t(0)',
            merge([merge([
                '    if !obj_val.Skip_%s {' % member[NAME],
                '        size += Rb_sizeof_%s(&obj_val.%s)' % (member[KEY].lower(), member[NAME].capitalize()),
                '        fields++',
                '    }',
                ]) for member in members]),
            '    size += Rb_seek_field_table_item(fields)',
            '    size += Sizeof_rb_buf_end',
            '    return size'
            ])
        }
    __encode = {
        'dec': lambda key, ctype: 'func Rb_encode_%s(obj_val *%s, rb_val *Rb_buf_t) bool' % (key.lower(), ctype.capitalize()),
        'imp': lambda key, ctype, members: merge([
            create_nested_buf('0'),
            merge([
                '    fields := Rb_field_size_t(Rb_fields_%s(obj_val))' % key.lower(),
                '    index := Rb_field_size_t(0)',
                '    if !Rb_set_field_count(fields, buf) { return false }',
                '',
                merge([merge([
                    '    if !obj_val.Skip_%s {' % member[NAME],
                    '        if !Rb_set_field_table_item(index, obj_val.Id_%s, Rb_offset_t(buf.Pos - buf.Start), buf) { return false }' % member[NAME],
                    '        if !Rb_encode_%s(&obj_val.%s, buf) { return false }' % (member[KEY].lower(), member[NAME].capitalize()),
                    '        index++'
                    '    }'
                    ]) for member in members]),
                '',
                '    if !Rb_set_buf_size(buf.Pos - buf.Start + Sizeof_rb_buf_end, buf) { return false }',
                '    if !Rb_encode_end(fields, buf) { return false }',
                '    rb_val.Pos = buf.Pos',
                '',
                '    return true'
                ])
            ])
        }
    __decode = {
        'dec': lambda key, ctype: 'func Rb_decode_%s(rb_val *Rb_buf_t, offset Rb_offset_t, obj_val *%s) bool' % (key.lower(), ctype.capitalize()),
        'private_imp': lambda key, ctype, members: merge([
            'func __decode_%s(' % key.lower(),
            '    item *Rb_field_table_item_t,',
            '    rb_val *Rb_buf_t,',
            '    obj_val *%s) bool {' % ctype.capitalize(),
            merge([merge([
                '    if item.Id == obj_val.Id_%s {' % member[NAME],
                '        rc := Rb_decode_%s(rb_val, item.Offset, &obj_val.%s)' % (member[KEY].lower(), member[NAME].capitalize()),
                '        if rc {',
                '            obj_val.Rb_has_%s = true' % member[NAME],
                '        }',
                '        return rc',
                '    }',
                ]) for member in members]),
            '    return true',
            '}',
            ''
            ]),
        'imp': lambda key, ctype, members: merge([
            '    if nil == obj_val {',
            '        return false',
            '    }',
            create_nested_buf('offset'),
            '    head := Rb_get_field_table_head(buf)',
            '    if head.Fields < 1 || !Rb_check_code(buf, head) {',
            '        return false',
            '    }',
            '    item := Rb_field_table_item_t{}',
            '    endoffset := Rb_offset_t(head.Size)',
            '    for i := Rb_field_size_t(0); i < head.Fields; i++ {',
            '        if !Rb_get_field_table_item(i, buf, &item) {',
            '            return false',
            '        }',
            '        if item.Offset >= endoffset {',
            '            return false',
            '        }',
            '        if item.Offset > 0 && !__decode_%s(&item, buf, obj_val) {' % key.lower(),
            '            return false',
            '        }',
            '    }',
            '    return true',
            ])
        }
    __dump = {
        'dec': lambda key, ctype: 'func Rb_dump_%s(obj_val *%s, path string) bool' % (key.lower(), ctype.capitalize()),
        'private_imp': lambda key, ctype, members: merge([
            'func __dump_%s(obj_val interface{}, buf *Rb_buf_t) bool {' % key.lower(),
            '    tmp_obj_val, ok := obj_val.(* %s)' % ctype.capitalize(),
            '    if !ok {',
            '        return false',
            '    }',
            '    return Rb_encode_%s(tmp_obj_val, buf)' % key.lower(),
            '}',
            ''
            ]),
        'imp': lambda key, ctype, members: merge([
            '    if nil == obj_val {',
            '        return false',
            '    }',
            '    size := Rb_sizeof_%s(obj_val)' % key.lower(),
            '    if size < 1 {',
            '        return false',
            '    }',
            '    return Rb_dump_buf(__dump_%s, obj_val, size, path)' % key.lower(),
            ])
        }
    __load = {
        'dec': lambda key, ctype: 'func Rb_load_%s(path string, obj_val *%s) bool' % (key.lower(), ctype.capitalize()),
        'private_imp': lambda key, ctype, members: merge([
            'func __load_%s(buf *Rb_buf_t, obj_val interface{}) bool {' % key.lower(),
            '    tmp_obj_val, ok := obj_val.(* %s)' % ctype.capitalize(),
            '    if !ok {',
            '        return false',
            '    }',
            '    return Rb_decode_%s(buf, 0, tmp_obj_val)' % key.lower(),
            '}',
            ''
            ]),
        'imp': lambda key, ctype, members: '    return Rb_load_buf(path, __load_%s, obj_val)' % key.lower()
        }
    return [__init, __set, __eq, __rb_fields, __sizeof, __encode, __decode, __dump, __load]

def gen_from_schema(path, obj, types, object_methods, array_methods, dict_methods):
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
    def __get_key(types, ctype):
        for type in types:
            if ctype == type['ctype']:
                return type['key']
        if ctype.endswith('_t'):
            return ctype[:(len(ctype) - len('_t'))]
        return ctype
    def __get_ctype(key, types):
        # do NOT support recursion!!!
        is_array = key.startswith('[') and key.endswith(']')
        is_dict = key.startswith('{') and key.endswith('}')
        if is_array:
            base_type = key[1:len(key) - 1]
            if 'string' == base_type:
                return 'String_array_t'
            return '%s_array_t' % __get_key(types, base_type).capitalize()
        if is_dict:
            base_type = key[1:len(key) - 1]
            if 'string' == base_type:
                return 'String_dict_t'
            return '%s_dict_t' % __get_key(types, base_type).capitalize()
        return key
    def __update_object(obj, types):
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
            struct['key'] = __get_key(types, struct['type'])
            struct['ctype'] = struct['type']
            __update_ids(struct['members'])
            for member in struct['members']:
                member[CTYPE] = __get_ctype(member[CTYPE], types)
                member.append(__get_key(types, member[CTYPE]))
    def __gen_implement(path, obj, types, object_methods, array_methods, dict_methods):
        def __get_object_type(types, ctype):
            for type in types:
                if ctype == type['ctype']:
                    return type['key']
            return ctype.capitalize()
        def __gen_struct(struct, types, object_methods, array_methods, dict_methods):
            __gen_def = lambda ctype, members: merge([
                'type %s struct {' % ctype.capitalize(),
                merge(['    %s %s' % (member[NAME].capitalize(), __get_object_type(types, member[CTYPE])) for member in members]),
                '',
                merge(['    Id_%s Rb_field_id_t' % member[NAME] for member in members]),
                '',
                merge(['    Skip_%s bool' % member[NAME] for member in members]),
                '',
                merge(['    Rb_has_%s bool' % member[NAME] for member in members]),
                '}',
                ''
                ])
            __gen_array_interface = lambda struct, array_methods, dict_methods: merge([
                '',
                gen_array_def(struct['key'], struct['ctype'], False),
                gen_dict_def(struct['key'], struct['ctype'], False),
                ''
                ]) if gen_array(struct) else FILTER
            __gen_imp = lambda key, ctype, members, method: merge([
                method['private_imp'](key, ctype, members) if 'private_imp' in method else FILTER,
                method['dec'](key, ctype) + ' {',
                method['imp'](key, ctype, members),
                '}',
                ''
                ])
            __gen_object_implement = lambda key, ctype, members, methods: merge([__gen_imp(key, ctype, members, method) for method in methods])
            __gen_array_imp = lambda key, ctype, methods: merge([
                gen_array_imp(key, ctype, method, False) for method in methods
                ])
            __gen_array_implement = lambda key, ctype, array_methods, dict_methods: merge([
                __gen_array_imp(key, ctype, array_methods),
                __gen_array_imp(key, ctype, dict_methods)
                ])
            return merge([
                __gen_def(struct['ctype'], struct['members']),
                __gen_array_interface(struct, array_methods, dict_methods),
                __gen_object_implement(struct['key'], struct['ctype'], struct['members'], object_methods),
                __gen_array_implement(struct['key'], struct['ctype'], array_methods, dict_methods) if gen_array(struct) else FILTER
                ])
        write_file(path + ".gen.go", merge([
            get_header(),
            'package rawbuf',
            '',
            merge([__gen_struct(struct, types, object_methods, array_methods, dict_methods) for struct in obj['structs']])
            ]))
    if not __check(obj['structs']):
        return False
    __update_object(obj, types)
    __gen_implement(path, obj, types, object_methods, array_methods, dict_methods)
    return True

def gen(file_list, types, str_t, object_methods, array_methods, dict_methods):
    full_types = list(types)
    full_types.append(str_t)
    for path_item in file_list:
        with open(path_item, 'r') as f:
            obj = json.load(f)
            gen_from_schema(
                path_item[:path_item.rfind('.')], 
                obj, 
                full_types,
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
            get_array_methods(array_frame, True, '&'),
            get_dict_methods(array_frame, True, '&'))
    op = argv[1]
    file_list = get_files(json_filter, op, argv[2:])
    return gen(
        file_list, 
        get_rb_types(), 
        get_rb_str_t(), 
        get_object_methods(),
        get_array_methods(array_frame, False, ''),
        get_dict_methods(array_frame, False, '')
        ) if len(file_list) > 0 else False

if __name__ == "__main__":
    if not parse_shell(sys.argv):
        manual()