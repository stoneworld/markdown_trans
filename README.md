# markdown_trans

## Preparation

1. Obtain an OpenAI API key
2. Ensure Python 3.8+ is installed.

## Usage

1. Install required dependencies by running pip install -r requirements.txt
2. Add your OpenAI API key on line 9 of mdoc.py
3. Run python mdoc.py -i input.md -o output.md to translate the input markdown file to English.

> Note: Currently, only English translation is supported.



# Markdown 文件翻译工具

## 准备工作

1. OpenAI API Token
2. Python 3.8+

## 使用方法

1. 使用命令 pip install -r requirements.txt 安装依赖包。
2. 在 mdoc.py 的第 9 行添加 OpenAI API Key。
3. 运行命令 python mdoc.py -i input.md -o output.md 进行转换。
4. 如果是整个目录下的 md，输出为当前目录下的 output 目录

> 目前只支持英语翻译功能，未来可能会添加其他语言的支持。可能会遇到很多其他的问题，欢迎 PR 


## Thanks
[@yihong0618](https://github.com/yihong0618)