[English](README.md)

# rawbuf - 高性能可伸缩的序列化库 #
![rawbuf logo](res/logo.png)

`rawbuf` 是一款 **全自动化** 的对象序列化神器，基于[YAS](https://github.com/jobs-github/yas)而全新设计的应用层数据协议。

`rawbuf` 的设计如下： 
![design](res/design.png)

## rawbuf是什么？ ##

`rawbuf` 项目的主要灵感来自[flatbuffers](https://github.com/google/flatbuffers)和[slothjson](https://github.com/jobs-github/slothjson)。`flatbuffers` 具有极致的性能，但是不够简单，`slothjson` 则正好相反。这正是 `rawbuf` 产出的原因。  
`rawbuf` 使用了类似于`flatbuffers`的二进制协议来描述数据格式，并基于[YAS](https://github.com/jobs-github/yas)规范来实现自动化。因此，其性能优于 `slothjson` ，且远比 `flatbuffers` 简单。  

更多详情，请参考[slothjson](https://github.com/jobs-github/slothjson)。

## rawbuf有什么？ ##

* 高性能 (比 `slothjson` 快4倍)  
* 简单、人性化的接口定义（一行代码搞定一切） 
* 简单、强大的代码生成器，支持全自动化（不用去手动码序列化的代码）
* 支持可选字段（可选字段编码、可选字段解码，无鸭梨）
* 灵活的数据描述文件（支持数组、字典、嵌套对象，以及**数组、字典的嵌套定义**）
* 设计简洁（没有使用复杂的 `C++` 模板技巧，阅读门槛很低），易复用，易扩展（支持新的类型极其容易）
* 跨平台（Windows & Linux & OS X）

## rawbuf怎么用？ ##

以 C++ 版本的实现为例，首先，你需要将以下内容放到你的项目中：

* `rawbuf`: 对应 `cpp/include/rawbuf.h` 和 `cpp/include/rawbuf.cpp`，`rawbuf` 的基础库

**以上就是全部的依赖**。  

然后，编写 `schema` 文件 `fxxx_gfw.json` 如下：

	{
	    "structs": 
	    [
	        {
	            "type": "fxxx_gfw_t",
	            "members": 
	            [
	                ["bool", "bool_val", "100"],
	                ["int8_t", "int8_val"],
	                ["int32_t", "int32_val"],
	                ["uint64_t", "uint64_val"],
	                ["double", "double_val", "101"],
	                ["string", "str_val"],
	                ["[int32_t]", "vec_val", "110"],
	                ["{string}", "dict_val"]
	            ]
	        }
	    ]
	}

运行如下命令：

    python cpp/generator/rawbuf.py -f cpp/src/fxxx_gfw.json

生成 `fxxx_gfw.h` 和 `fxxx_gfw.cpp` 之后，将它们添加到你的项目中。  
接下来你可以这样编写序列化的代码：

    rawbuf::fxxx_gfw_t obj_val;
    // 设置obj_val的内容
    ......
    // 输出为rb_buf_t的实例
	rawbuf::rb_buf_t rb_val = rawbuf::rb_create_buf(rawbuf::rb_sizeof(obj_val));
	bool rc = rawbuf::rb_encode(obj_val, rb_val);
	// 使用rb_val的值
	......
	rawbuf::rb_dispose_buf(rb_val); // 别忘记释放资源！
    // 输出为文件
    std::string path = "fxxx_gfw_t.bin";
    bool rc = rawbuf::rb_dump(obj_val, path);

如果不想序列化全部字段，可以这样编写：

    obj_val.skip_dict_val(); // 调用 skip_xxx 方法
反序列化的代码类似：

	rawbuf::rb_buf_t rb_val = rawbuf::rb_create_buf(rawbuf::rb_sizeof(obj_val));
    // 设置rb_val的内容
    ......
	// 从rb_val中加载
    rawbuf::fxxx_gfw_t obj_val;
	bool rc = rawbuf::rb_decode(rb_val, 0, obj_val);
	......
	rawbuf::rb_dispose_buf(rb_val); // 别忘记释放资源！

    // 从文件中加载
	std::string path = "fxxx_gfw_t.bin";
    rawbuf::fxxx_gfw_t obj_val;
	bool rc = rawbuf::rb_load(path, obj_val);

如果想判断指定的字段 **是否在原始的二进制buffer中**，可以这样编写：

    if (obj_val.rb_has_dict_val()) // 调用 rb_has_xxx() 方法
    {
         ......
    }

以上就是 `rawbuf` 的用法，很简单吧？  

## rawbuf支持哪些编程语言？ ##

* C++
* C
* Go

我实现了`rawbuf`的`php`和`python`的版本，但由于性能问题，并未合并到主分支。欢迎贡献其他语言的`rawbuf`的高性能的实现。  

* [php-alpha](https://github.com/jobs-github/rawbuf/tree/php-alpha)  
* [python-alpha](https://github.com/jobs-github/rawbuf/tree/python-alpha)  
* [php-beta](https://github.com/jobs-github/rawbuf/tree/php-beta)  
* [python-beta](https://github.com/jobs-github/rawbuf/tree/python-beta)  

备注：`beta`分支的性能优于`alpha`分支的性能。

## 对于 YAS 扩展的实现 ##

语言          | 是否实现 YAS 扩展
--------------|-------------------------
C++           |         是
C             |         否
go            |         否
php-alpha     |         是
python-alpha  |         是
php-beta      |         否
python-beta   |         否

## rawbuf支持哪些平台？ ##

Platform | Description
---------|----------------------------------------------------------
Linux    | CentOS 6.x & Ubuntu 10.04 (kernel 2.6.32) GCC 4.4.7
Win32    | Windows 7, MSVC 10.0
OS X     | Mac OS X EI Capitan, GCC 4.2.1, Apple LLVM version 7.3.0

## 性能 ##



## 进阶 ##

`rawbuf` 和 `slothjson` 使用了 **相同的设计和数据描述文件**。它们之间的差异在于协议（文本 vs 二进制）和性能。

更多详情，请参考[这里](https://github.com/jobs-github/slothjson) 和 [这里](https://github.com/jobs-github/yas)

## 协议设计 ##

### scalar ###
![scalar](res/scalar.png)

### string ###
![string](res/string.png)

### object ###
![object](res/object.png)

### array ###
![array](res/array.png)

### dict ###
![dict](res/dict.png)

## License ##

`rawbuf` is licensed under [New BSD License](https://opensource.org/licenses/BSD-3-Clause), a very flexible license to use.

## 作者 ##

* chengzhuo (jobs, yao050421103@163.com)  

## 更多 ##

- Yet Another Schema - [YAS](https://github.com/jobs-github/yas)  
- 为懒人打造的json对象序列化神器 - [slothjson](https://github.com/jobs-github/slothjson)  
- 高性能分布式存储服务 - [huststore](https://github.com/Qihoo360/huststore)  