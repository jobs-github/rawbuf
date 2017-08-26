<?php

function rb_is_little_endian()
{
    static $_is_little_endian = null;
    if ($_is_little_endian === null)
    {
        $rc = unpack('S', "\x01\x00");
        $_is_little_endian = ($rc[1] === 1);
    }
    return $_is_little_endian;
}

function rb_write_little_endian($data, $offset, $count, $buf)
{
    if (rb_is_little_endian())
    {
        for ($i = 0; $i < $count; $i++)
        {
            $buf->data[$offset + $i] = chr($data >> $i * 8);
        }
    }
    else
    {
        for ($i = 0; $i < $count; $i++)
        {
            $buf->data[$offset + $count - 1 - $i] = chr($data >> $i * 8);
        }
    }
}

function rb_read_little_endian($buf, $offset, $count)
{
    $r = 0;
    if (rb_is_little_endian())
    {
        for ($i = 0; $i < $count; $i++)
        {
            $r |= ord($buf->data[$offset + $i]) << $i * 8;
        }
    }
    else
    {
        for ($i = 0; $i < $count; $i++)
        {
            $r |= ord($buf->data[$offset + $count -1 - $i]) << $i * 8;
        }
    }
    return $r;
}

function rb_pack_base($format, $data, $offset, $count, $buf)
{
    $bstr = pack($format, $data);
    for($i = 0; $i < $count; ++$i)
    {
        $buf->data[$offset + $i] = $bstr[$i];
    }
}

function rb_unpack_base($format, $buf, $offset, $count)
{
    $bstr = substr($buf->data, $offset, $count);
    $data = unpack($format, $bstr);
    return $data[1];
}

function rb_write_int8($data, $offset, $count, $buf)
{
    rb_pack_base('c', $data, $offset, $count, $buf);
}

function rb_read_int8($buf, $offset, $count)
{
    return rb_unpack_base('c', $buf, $offset, $count);
}

function rb_write_uint8($data, $offset, $count, $buf)
{
    rb_pack_base('C', $data, $offset, $count, $buf);
}

function rb_read_uint8($buf, $offset, $count)
{
    return rb_unpack_base('C', $buf, $offset, $count);
}

function rb_read_bool($buf, $offset, $count)
{
    return (bool) rb_read_uint8($buf, $offset, $count);
}

function rb_read_int16($buf, $offset, $count)
{
    $result = rb_read_little_endian($buf, $offset, $count);
    $sign = $offset + (rb_is_little_endian() ? 1 : 0);
    $issigned = isset($buf->data[$sign]) && ord($buf->data[$sign]) & 0x80;
    // 65536 = 1 << 16 = Maximum unsigned 16-bit int
    return $issigned ? $result - 65536 : $result;
}

function rb_write_uint16($data, $offset, $count, $buf)
{
    rb_pack_base('v', $data, $offset, $count, $buf);
}

function rb_read_int32($buf, $offset, $count)
{
    $result = rb_read_little_endian($buf, $offset, $count);

    $sign = $offset + (rb_is_little_endian() ? 3 : 0);
    $issigned = isset($buf->data[$sign]) && ord($buf->data[$sign]) & 0x80;

    if (PHP_INT_SIZE > 4)
    {
        // 4294967296 = 1 << 32 = Maximum unsigned 32-bit int
        return $issigned ? $result - 4294967296 : $result;
    }
    else
    {
        // 32bit / Windows treated number as signed integer.
        return $result;
    }
}

function rb_read_uint16($buf, $offset, $count)
{
    return rb_unpack_base('v', $buf, $offset, $count);
}

function rb_write_uint32($data, $offset, $count, $buf)
{
    rb_pack_base('V', $data, $offset, $count, $buf);
}

function rb_read_uint32($buf, $offset, $count)
{
    return rb_unpack_base('V', $buf, $offset, $count);
}

function rb_write_string($data, $offset, $count, $buf)
{
    $packer_type = 'a' . strval($count);
    rb_pack_base($packer_type, $data, $offset, $count, $buf);
}

function rb_read_string($buf, $offset, $count)
{
    $packer_type = 'a' . strval($count);
    $bstr = substr($buf->data, $offset, $count);
    $data = unpack($packer_type, $bstr);
    return $data;
}

function rb_write_float($data, $offset, $count, $buf)
{
    $floathelper = pack("f", $data);
    $v = unpack("V", $floathelper);
    rb_write_little_endian($v[1], $offset, 4, $buf);
}

function rb_read_float($buf, $offset, $count)
{
    $value = rb_read_little_endian($buf, $offset, 4);
    $inthelper = pack("V", $value);
    $v = unpack("f", $inthelper);
    return $v[1];
}

function rb_write_double($data, $offset, $count, $buf)
{
    $floathelper = pack("d", $data);
    $v = unpack("V*", $floathelper);
    rb_write_little_endian($v[1], $offset, 4, $buf);
    rb_write_little_endian($v[2], $offset + 4, 4, $buf);
}

function rb_read_double($buf, $offset, $count)
{
    $value = rb_read_little_endian($buf, $offset, 4);
    $value2 = rb_read_little_endian($buf, $offset + 4, 4);
    $inthelper = pack("VV", $value, $value2);
    $v = unpack("d", $inthelper);
    return $v[1];
}

class bool_flags_t
{
    public static $bytewidth = 1;
    public static $min_val = false;
    public static $max_val = true;
    public static $def_val = false;
    public static $writer = rb_write_uint8;
    public static $reader = rb_read_bool;
}
class int8_flags_t
{
    public static $bytewidth = 1;
    public static $min_val = - 128;
    public static $max_val = 127;
    public static $def_val = 0;
    public static $writer = rb_write_int8;
    public static $reader = rb_read_int8;
}
class uint8_flags_t
{
    public static $bytewidth = 1;
    public static $min_val = 0;
    public static $max_val = 255;
    public static $def_val = 0;
    public static $writer = rb_write_uint8;
    public static $reader = rb_read_uint8;
}
class int16_flags_t
{
    public static $bytewidth = 2;
    public static $min_val = - 32768;
    public static $max_val = 32767;
    public static $def_val = 0;
    public static $writer = rb_write_little_endian;
    public static $reader = rb_read_int16;
}
class uint16_flags_t
{
    public static $bytewidth = 2;
    public static $min_val = 0;
    public static $max_val = 65535;
    public static $def_val = 0;
    public static $writer = rb_write_uint16;
    public static $reader = rb_read_uint16;
}
class int32_flags_t
{
    public static $bytewidth = 4;
    public static $min_val = - 2147483648;
    public static $max_val = 2147483647;
    public static $def_val = 0;
    public static $writer = rb_write_little_endian;
    public static $reader = rb_read_int32;
}
class uint32_flags_t
{
    public static $bytewidth = 4;
    public static $min_val = 0;
    public static $max_val = 4294967295;
    public static $def_val = 0;
    public static $writer = rb_write_uint32;
    public static $reader = rb_read_uint32;
}

// php version >= 5.6.3
class int64_flags_t
{
    public static $bytewidth = 8;
    public static $min_val = PHP_INT_MIN;
    public static $max_val = PHP_INT_MAX;
    public static $def_val = 0;
    public static $writer = rb_write_little_endian;
    public static $reader = rb_read_little_endian;
}

// php version >= 5.6.3
class uint64_flags_t
{
    public static $bytewidth = 8;
    public static $min_val = 0;
    public static $max_val = PHP_INT_MAX;
    public static $def_val = 0;
    public static $writer = rb_write_little_endian;
    public static $reader = rb_read_little_endian;
}
class float_flags_t
{
    public static $bytewidth = 4;
    public static $min_val = null;
    public static $max_val = null;
    public static $def_val = 0.0;
    public static $writer = rb_write_float;
    public static $reader = rb_read_float;
}
class double_flags_t
{
    public static $bytewidth = 8;
    public static $min_val = null;
    public static $max_val = null;
    public static $def_val = 0.0;
    public static $writer = rb_write_double;
    public static $reader = rb_read_double;
}

class rb_number_t
{
    public $flags;
    public $val;
    private $__val;
    public function __construct($flags, $val)
    {
        $this->flags = $flags;
        $this->__val = $flags::$def_val;
        if (null == $val)
        {
            $this->val = $this->__val;
        }
        else
        {
            $this->enforce_number($val, $this->flags);
            $this->val = $val;
        }
    }
    private function enforce_number($val, $flags)
    {
        if (null == $flags::$min_val && null == $flags::$max_val)
        {
            return;
        }
        if (!($flags::$min_val <= $val && $val <= $flags::$max_val))
        {
            throw new \Exception("bad number");
        }
    }
    private function writer()
    {
        $flags = $this->flags;
        return $flags::$writer;
    }
    private function reader()
    {
        $flags = $this->flags;
        return $flags::$reader;
    }
    public function eq($other)
    {
        if ($other instanceof rb_number_t)
        {
            return $this->flags == $other->flags && $this->val == $other->val;
        }
        return $this->val == $other;
    }
    public function assign($other)
    {
        if ($other instanceof rb_number_t)
        {
            if ($this->flags != $other->flags)
            {
                throw new \Exception("bad flags");
            }
            $this->val = $other->val;
        }
        else
        {
            $this->val = $other;
        }
    }
    public function reset()
    {
        $this->val = $this->__val;
    }
    public function rb_size()
    {
        $flags = $this->flags;
        return $flags::$bytewidth;
    }
    public function rb_encode($rb_val)
    {
        $size = $this->rb_size();
        if (!rawbuf::rb_encode_check($rb_val, $size))
        {
            return false;
        }
        rawbuf::to_memory($this->writer(), $this->rb_size(), $rb_val, $rb_val->pos, $this->val);
        $rb_val->pos += $size;
        return true;
    }
    public function rb_decode($rb_val, $offset)
    {
        $size = $this->rb_size();
        if (!rawbuf::rb_decode_check($rb_val, $offset, $size))
        {
            return false;
        }
        $flags = $this->flags;
        $this->val = rawbuf::from_memory($this->reader(), $this->rb_size(), $rb_val, $rb_val->start + $offset);
        return true;
    }
}
class rb_scalar_t
{
    public static function writer($type)
    {
        $flags = $type::get_flags();
        return $flags::$writer;
    }
    public static function reader($type)
    {
        $flags = $type::get_flags();
        return $flags::$reader;
    }
    public static function rb_size($type)
    {
        $flags = $type::get_flags();
        return $flags::$bytewidth;
    }
    public static function rb_write($type, $buf, $offset, $data)
    {
        rawbuf::to_memory(self::writer($type), self::rb_size($type), $buf, $offset, $data);
        return true;
    }
    public static function rb_read($type, $buf, $offset)
    {
        return rawbuf::from_memory(self::reader($type), self::rb_size($type), $buf, $offset);
    }
}
class rb_type_pair_t
{
    private $elem_type;
    private $base_type;
    public function __construct($type_pair = array())
    {
        $this->elem_type = $type_pair[0];
        $this->base_type = $type_pair[1];
    }
    public function create_item()
    {
        return (null === $this->base_type) ? (new $this->elem_type()) : (new $this->elem_type($this->base_type));
    }
}
class rawbuf
{
    public static function rb_crc32($buf, $fields)
    {
        $offset = rb_seek_field_table_item($fields);
        return crc32(substr($buf->data, $buf->start, $offset));
    }
    public static function from_memory($reader, $rb_size, $buf, $offset)
    {
        return $reader($buf, $offset, $rb_size);
    }
    public static function to_memory($writer, $rb_size, $buf, $offset, $data)
    {
        $writer($data, $offset, $rb_size, $buf);
    }
    public static function rb_check_buf($buf)
    {
        return ($buf->size > 0) && ($buf->pos >= $buf->start) && ($buf->pos <= $buf->end) && ($buf->start + $buf->size <= $buf->end);
    }
    public static function rb_encode_check($buf, $size)
    {
        return self::rb_check_buf($buf) && ($buf->pos + $size < $buf->end);
    }
    public static function rb_decode_check($buf, $offset, $size)
    {
        return self::rb_check_buf($buf) && ($buf->start + $offset + $size < $buf->end) && ($offset + $size < $buf->size);
    }
    public static function rb_make_buf($data, $size)
    {
        $buf = new rb_buf_t();
        $buf->data = &$data;
        $buf->start = 0;
        $buf->size = $size;
        $buf->pos = $buf->start;
        $buf->end = $buf->start + $buf->size;
        return $buf;
    }
    public static function rb_nested_buf($buf, $offset)
    {
        $nested_buf = new rb_buf_t();
        if (self::rb_check_buf($buf))
        {
            $nested_buf->data = &$buf->data;
            $nested_buf->start = (0 == $offset) ? $buf->pos : ($buf->start + $offset);
            $nested_buf->end = $buf->end;
            $nested_buf->pos = $nested_buf->start;
            $nested_buf->size = $nested_buf->end - $nested_buf->start;
        }
        return $nested_buf;
    }
    public static function rb_seek_array_table_item($index)
    {
        return rb_scalar_t::rb_size(rb_size_t) + $index * rb_scalar_t::rb_size(rb_offset_t);
    }
    public static function rb_set_array_count($size, $rb_val)
    {
        if (!self::rb_check_buf($rb_val))
        {
            return false;
        }
        if ($rb_val->pos + rb_scalar_t::rb_size(rb_size_t) > $rb_val->end)
        {
            return false;
        }
        rb_scalar_t::rb_write(rb_size_t, $rb_val, $rb_val->pos, $size);
        $rb_val->pos = $rb_val->start + self::rb_seek_array_table_item($size);
        if ($rb_val->pos > $rb_val->end)
        {
            return false;
        }
        return true;
    }
    public static function rb_get_array_count($rb_val)
    {
        $pos = $rb_val->start;
        if ($pos + rb_scalar_t::rb_size(rb_size_t) < $rb_val->end)
        {
            return rb_scalar_t::rb_read(rb_size_t, $rb_val, $pos);
        }
        return 0;
    }
    public static function rb_set_array_table_item($index, $offset, $rb_val)
    {
        $pos = $rb_val->start + self::rb_seek_array_table_item($index);
        if ($pos + rb_scalar_t::rb_size(rb_offset_t) > $rb_val->end)
        {
            return false;
        }
        rb_scalar_t::rb_write(rb_offset_t, $rb_val, $pos, $offset);
        return true;
    }
    public static function rb_get_array_table_item($index, $rb_val)
    {
        $pos = $rb_val->start + self::rb_seek_array_table_item($index);
        if (pos + rb_scalar_t::rb_size(rb_offset_t) > $rb_val->end)
        {
            return array(false, 0);
        }
        return array(true, rb_scalar_t::rb_read(rb_offset_t, $rb_val, $pos));
    }
    public static function rb_sizeof_str($obj_val)
    {
        return rb_scalar_t::rb_size(rb_size_t) + strlen($obj_val);
    }
    public static function rb_encode_str($obj_val, $rb_val)
    {
        if (!self::rb_encode_check($rb_val, self::rb_sizeof_str($obj_val)))
        {
            return false;
        }
        $size = strlen($obj_val);
        rb_scalar_t::rb_write(rb_size_t, $rb_val, $rb_val->pos, $size);
        $rb_val->pos += rb_scalar_t::rb_size(rb_size_t);
        if ($size > 0)
        {
            self::to_memory(rb_write_string, $size, $rb_val, $rb_val->pos, $obj_val);
            $rb_val->pos += $size;
        }
        return true;
    }
    public static function rb_decode_str($rb_val, $offset)
    {
        $size = rb_scalar_t::rb_size(rb_size_t);
        if (!self::rb_decode_check($rb_val, $offset, $size))
        {
            return array(false, '');
        }
        $obj_len = rb_scalar_t::rb_read(rb_size_t, $rb_val, $rb_val->start + $offset);
        if ($obj_len > 0)
        {
            $off = $offset + $size;
            if (!self::rb_decode_check($rb_val, $off, $obj_len))
            {
                return array(false, '');
            }
            $bytes = self::from_memory(rb_read_string, $obj_len, $rb_val, $rb_val->start + $off);
            return array(true, join('', $bytes));
        }
    }
    public static function rb_set_field_table_item($index, $id, $offset, $rb_val)
    {
        $pos = $rb_val->start + rb_seek_field_table_item($index);
        $size = rb_field_table_item_size();
        if ($pos + $size > $rb_val->end)
        {
            return false;
        }
        rb_scalar_t::rb_write(rb_field_id_t, $rb_val, $pos, $id);
        rb_scalar_t::rb_write(rb_offset_t, $rb_val, $pos + rb_scalar_t::rb_size(rb_field_id_t), $offset);
        return true;
    }
    public static function rb_set_buf_size($size, $rb_val)
    {
        if ($rb_val->start + rb_scalar_t::rb_size(rb_size_t) > $rb_val->end)
        {
            return false;
        }
        rb_scalar_t::rb_write(rb_size_t, $rb_val, $rb_val->start, $size);
        return true;
    }
    public static function rb_set_field_count($fields, $rb_val)
    {
        $head_size = rb_field_table_head_size();
        if ($rb_val->start + $head_size > $rb_val->end)
        {
            return false;
        }
        $offset = $rb_val->start + $head_size - rb_scalar_t::rb_size(rb_field_size_t);
        rb_scalar_t::rb_write(rb_field_size_t, $rb_val, $offset, $fields);
        $rb_val->pos = $rb_val->start + rb_seek_field_table_item($fields);
        if ($rb_val->pos > $rb_val->end)
        {
            return false;
        }
        return true;
    }
    public static function rb_encode_end($fields, $rb_val)
    {
        $size = rb_scalar_t::rb_size(rb_buf_end_t);
        if (!rawbuf::rb_check_buf($rb_val) || ($rb_val->pos + $size > $rb_val->end))
        {
            return false;
        }
        $end = rawbuf::rb_crc32($rb_val, $fields);
        rb_scalar_t::rb_write(rb_buf_end_t, $rb_val, $rb_val->pos, $end);
        $rb_val->pos += $size;
        return true;
    }
    public static function rb_check_code($buf, $size, $fields)
    {
        if (!rawbuf::rb_check_buf($buf))
        {
            return false;
        }
        if (($buf->start + $size > $buf->end) || ($size > $buf->size))
        {
            return false;
        }
        $pos = $buf->start + $size - rb_scalar_t::rb_size(rb_buf_end_t);
        $end = rb_scalar_t::rb_read(rb_buf_end_t, $buf, $pos);
        $checkcode = rawbuf::rb_crc32($buf, $fields);
        if ($end != $checkcode)
        {
            return false;
        }
        return true;
    }
}

class rb_bool_t extends rb_number_t
{
    public static function get_flags()
    {
        return bool_flags_t;
    }
    public function __construct($val = null)
    {
        parent::__construct(self::get_flags(), $val);
    }
}
class rb_int8_t extends rb_number_t
{
    public static function get_flags()
    {
        return int8_flags_t;
    }
    public function __construct($val = null)
    {
        parent::__construct(self::get_flags(), $val);
    }
}
class rb_uint8_t extends rb_number_t
{
    public static function get_flags()
    {
        return uint8_flags_t;
    }
    public function __construct($val = null)
    {
        parent::__construct(self::get_flags(), $val);
    }
}
class rb_int16_t extends rb_number_t
{
    public static function get_flags()
    {
        return int16_flags_t;
    }
    public function __construct($val = null)
    {
        parent::__construct(self::get_flags(), $val);
    }
}
class rb_uint16_t extends rb_number_t
{
    public static function get_flags()
    {
        return uint16_flags_t;
    }
    public function __construct($val = null)
    {
        parent::__construct(self::get_flags(), $val);
    }
}
class rb_int32_t extends rb_number_t
{
    public static function get_flags()
    {
        return int32_flags_t;
    }
    public function __construct($val = null)
    {
        parent::__construct(self::get_flags(), $val);
    }
}
class rb_uint32_t extends rb_number_t
{
    public static function get_flags()
    {
        return uint32_flags_t;
    }
    public function __construct($val = null)
    {
        parent::__construct(self::get_flags(), $val);
    }
}
class rb_int64_t extends rb_number_t
{
    public static function get_flags()
    {
        return int64_flags_t;
    }
    public function __construct($val = null)
    {
        parent::__construct(self::get_flags(), $val);
    }
}
class rb_uint64_t extends rb_number_t
{
    public static function get_flags()
    {
        return uint64_flags_t;
    }
    public function __construct($val = null)
    {
        parent::__construct(self::get_flags(), $val);
    }
}
class rb_float_t extends rb_number_t
{
    public static function get_flags()
    {
        return float_flags_t;
    }
    public function __construct($val = null)
    {
        parent::__construct(self::get_flags(), $val);
    }
}
class rb_double_t extends rb_number_t
{
    public static function get_flags()
    {
        return double_flags_t;
    }
    public function __construct($val = null)
    {
        parent::__construct(self::get_flags(), $val);
    }
}

class_alias(rb_uint32_t, rb_size_t);
class_alias(rb_uint8_t, rb_field_size_t);
class_alias(rb_field_size_t, rb_field_id_t);
class_alias(rb_size_t, rb_offset_t);
class_alias(rb_uint32_t, rb_buf_end_t);

function rb_field_table_head_size()
{
    static $size = null;
    if (null === $size)
    {
        $size = rb_scalar_t::rb_size(rb_size_t) + rb_scalar_t::rb_size(rb_field_size_t);
    }
    return $size;
}

function rb_field_table_item_size()
{
    static $size = null;
    if (null === $size)
    {
        $size = rb_scalar_t::rb_size(rb_field_id_t) + rb_scalar_t::rb_size(rb_offset_t);
    }
    return $size;
}

class rb_buf_t
{
    public $size = null;
    public $start = null;
    public $pos = null;
    public $end = null;
    public $data = null;
}

function rb_create_buf($size)
{
    $buf = new rb_buf_t();
    $buf->size = $size;
    $buf->data = str_repeat("\0", $size);
    $buf->start = 0;
    $buf->pos = $buf->start;
    $buf->end = $buf->start + $buf->size;
    return $buf;
}

function rb_seek_field_table_item($index)
{
    return rb_field_table_head_size() + $index * rb_field_table_item_size();
}

class rb_string_t
{
    public $val = '';
    public function __construct($val = '')
    {
        if (!is_string($val))
        {
            throw new \Exception("invalid type");
        }
        $this->val = $val;
    }
    public function eq($other)
    {
        if (is_string($other))
        {
            return $this->val == $other;
        }
        elseif ($other instanceof rb_string_t)
        {
            return $this->val == $other->val;
        }
        return false;
    }
    public function size()
    {
        return strlen($this->val);
    }
    public function assign($other)
    {
        if (is_string($other))
        {
            $this->val = $other;
        }
        elseif ($other instanceof rb_string_t)
        {
            $this->val = $other->val;
        }
        else
        {
            throw new \Exception("invalid type");
        }
    }
    public function reset()
    {
        $this->val = '';
    }
    public function rb_size()
    {
        return rawbuf::rb_sizeof_str($this->val);
    }
    public function rb_encode($rb_val)
    {
        return rawbuf::rb_encode_str($this->val, $rb_val);
    }
    public function rb_decode($rb_val, $offset)
    {
        list($rc, $this->val) = rawbuf::rb_decode_str($rb_val, $offset);
        return $rc;
    }
}

class rb_list_t extends ArrayObject
{
    private $type_pair;
    public function __construct($type_pair, $value = array())
    {
        $this->type_pair = new rb_type_pair_t($type_pair);
        parent::__construct($value);
    }
    public function eq($other)
    {
        if (!($other instanceof rb_list_t))
        {
            return false;
        }
        $src_size = $this->size();
        $dst_size = $other->size();
        if ($src_size != $dst_size)
        {
            return false;
        }
        foreach($this as $index => $item)
        {
            if (!$item->eq($other[$index]))
            {
                return false;
            }
        }
        return true;
    }
    public function assign($other)
    {
        $this->exchangeArray($other);
    }
    public function size()
    {
        return count($this);
    }
    public function reset()
    {
        static $empty = null;
        if (null == $empty)
        {
            $empty = array();
        }
        $this->exchangeArray($empty);
    }
    public function rb_size()
    {
        $array_count = $this->size();
        $size = rb_scalar_t::rb_size(rb_size_t) + $array_count * rb_scalar_t::rb_size(rb_size_t);
        foreach($this as $item)
        {
            $size += $item->rb_size();
        }
        return $size;
    }
    public function rb_encode($rb_val)
    {
        $buf = rawbuf::rb_nested_buf($rb_val, 0);
        if ($buf->size < 1)
        {
            return false;
        }
        $array_count = $this->size();
        if (!rawbuf::rb_set_array_count($array_count, $buf))
        {
            return false;
        }
        foreach($this as $index => $item)
        {
            if (!rawbuf::rb_set_array_table_item($index, $buf->pos - $buf->start, $buf))
            {
                return false;
            }
            if (!$item->rb_encode($buf))
            {
                return false;
            }
        }
        $rb_val->pos = $buf->pos;
        return true;
    }
    public function rb_decode($rb_val, $offset)
    {
        $buf = rawbuf::rb_nested_buf($rb_val, $offset);
        if ($buf->size < 1)
        {
            return false;
        }
        $size = rawbuf::rb_get_array_count($buf);
        if ($size < 1)   
        {
            return true;
        }
        for ($i = 0; $i < $size; ++$i)
        {
            list($rc, $off) = rawbuf::rb_get_array_table_item($i, $buf);
            if (!$rc)
            {
                return false;
            }
            $type_pair = $this->type_pair;
            $tmp_obj_val = $type_pair->create_item();
            if (!$tmp_obj_val->rb_decode($buf, $off))
            {
                return false;
            }
            $this->append($tmp_obj_val);
        }
        return true;
    }
}

class rb_dict_t extends ArrayObject
{
    private $type_pair;
    public function __construct($type_pair, $value = array())
    {
        $this->type_pair = new rb_type_pair_t($type_pair);
        parent::__construct($value);
    }
    public function assign($other)
    {
        $this->exchangeArray($other);
    }
    public function eq($other)
    {
        if (!($other instanceof rb_dict_t))
        {
            return false;
        }
        $src_size = $this->size();
        $dst_size = $other->size();
        if ($src_size != $dst_size)
        {
            return false;
        }
        foreach($this as $key => $item)
        {
            $val = $other[$key];
            if (null == $val)
            {
                return false;
            }
            if (!$item->eq($val))
            {
                return false;
            }
        }
        return true;
    }
    public function size()
    {
        return count($this);
    }
    public function reset()
    {
        static $empty = null;
        if (null == $empty)
        {
            $empty = array();
        }
        $this->exchangeArray($empty);
    }
    public function rb_size()
    {
        $array_count = $this->size();
        $size = rb_scalar_t::rb_size(rb_size_t) + $array_count * rb_scalar_t::rb_size(rb_size_t);
        foreach($this as $key => $item)
        {
            $size += rawbuf::rb_sizeof_str($key);
            $size += $item->rb_size();
        }
        return $size;
    }
    public function rb_encode($rb_val)
    {
        $buf = rawbuf::rb_nested_buf($rb_val, 0);
        if ($buf->size < 1)
        {
            return false;
        }
        $array_count = $this->size();
        if (!rawbuf::rb_set_array_count($array_count, $buf))
        {
            return false;
        }
        $i = 0;
        foreach($this as $key => $item)
        {
            if (!rawbuf::rb_set_array_table_item($i, $buf->pos - $buf->start, $buf))
            {
                return false;
            }
            if (!rawbuf::rb_encode_str($key, $buf))
            {
                return false;
            }
            if (!$item->rb_encode($buf))
            {
                return false;
            }
            ++$i;
        }
        $rb_val->pos = $buf->pos;
        return true;
    }
    public function rb_decode($rb_val, $offset)
    {
        $buf = rawbuf::rb_nested_buf($rb_val, $offset);
        if ($buf->size < 1)
        {
            return false;
        }
        $size = rawbuf::rb_get_array_count($buf);
        if ($size < 1)
        {
            return true;
        }
        for ($i = 0; $i < $size; ++$i)
        {
            list($rc, $off) = rawbuf::rb_get_array_table_item($i, $buf);
            if (!$rc)
            {
                return false;
            }
            list($rc, $key) = rawbuf::rb_decode_str($buf, $off);
            if (!$rc)
            {
                return false;
            }
            $type_pair = $this->type_pair;
            $val = $type_pair->create_item();
            if (!$val->rb_decode($buf, $off + rawbuf::rb_sizeof_str($key)))
            {
                return false;
            }
            $this[$key] = $val;
        }
        return true;
    }
}

function rb_encode_field($index, $id, $field, $buf)
{
    if (!rawbuf::rb_set_field_table_item($index, $id, $buf->pos - $buf->start, $buf))
    {
        return False;
    }
    if (!$field->rb_encode($buf))
    {
        return false;
    }
    return true;
}

function rb_decode_field($field_id, $id, $offset, $rb_val, $rc, $rb_has_field, $field)
{
    if ($id == $field_id)
    {
        $rc->val = $field->rb_decode($rb_val, $offset);
        if ($rc->val)
        {
            $rb_has_field->val = true;
        }
        return true;
    }
    return false;
}

function rb_encode_base($obj_val, $rb_val)
{
    $fields = $obj_val->rb_fields();
    $buf = rawbuf::rb_nested_buf($rb_val, 0);
    if ($buf->size < 1)
    {
        return false;
    }
    if (!rawbuf::rb_set_field_count($fields, $buf))
    {
        return false;
    }
    if (!$obj_val->encode($buf))
    {
        return false;
    }
    if (!rawbuf::rb_set_buf_size($buf->pos - $buf->start + rb_scalar_t::rb_size(rb_buf_end_t), $buf))
    {
        return false;
    }
    if (!rawbuf::rb_encode_end($fields, $buf))
    {
        return false;
    }
    $rb_val->pos = $buf->pos;
    return true;
}

function rb_decode_base($rb_val, $offset, $obj_val)
{
    $buf = rawbuf::rb_nested_buf($rb_val, $offset);
    if ($buf->size < 1)
    {
        return false;
    }
    if (!rawbuf::rb_decode_check($buf, 0, rb_field_table_head_size()))
    {
        return false;
    }
    $buf_size = rb_scalar_t::rb_read(rb_size_t, $buf, $buf->start);
    $fields = rb_scalar_t::rb_read(rb_field_size_t, $buf, $buf->start + rb_scalar_t::rb_size(rb_size_t));
    if ($fields < 1 || !rawbuf::rb_check_code($buf, $buf_size, $fields))
    {
        return false;
    }
    for ($i = 0; $i < $fields; ++$i)
    {
        $pos = $buf->start + rb_seek_field_table_item($i);
        $size = rb_field_table_item_size();
        if ($pos + $size > $buf->end)
        {
            return false;
        }
        $field_id = rb_scalar_t::rb_read(rb_field_id_t, $buf, $pos);
        $field_off = rb_scalar_t::rb_read(rb_offset_t, $buf, $pos + rb_scalar_t::rb_size(rb_field_id_t));
        if ($field_off >= $buf_size)
        {
            return false;
        }
        if ($field_off > 0 && ! $obj_val->decode($field_id, $field_off, $buf))
        {
            return false;
        }
    }
    return true;
}

function rb_dump_base($obj_val, $path)
{
    $size = $obj_val->rb_size();
    if ($size < 1)
    {
        return false;
    }
    $buf = rb_create_buf($size);
    if (!$obj_val->rb_encode($buf))
    {
        return false;
    }
    $len = file_put_contents($path, $buf->data);
    return $len == $size;
}

function rb_load_base($path, $obj_val)
{
    $file_size = filesize($path);
    if ($file_size < 1)
    {
        return false;
    }
    $data = file_get_contents($path);
    $buf = rawbuf::rb_make_buf($data, $file_size);
    $size = rb_scalar_t::rb_read(rb_size_t, $buf, 0);
    if ($size < 1 || $size > $file_size)
    {
        return false;
    }
    $buf = rawbuf::rb_make_buf($data, $size);
    return $obj_val->rb_decode($buf, 0);
}

?>