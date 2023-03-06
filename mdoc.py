import re
import time
import openai
import requests
import argparse
import os
import markdown

NO_LIMIT = False
API_KEY = "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"


class ChatGPT:
    def __init__(self, key, language, api_base=None):
        self.key = key
        self.language = language
        self.current_key_index = 0
        if api_base:
            openai.api_base = api_base

    def get_key(self, key_str):
        keys = key_str.split(",")
        key = keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(keys)
        return key

    def translate(self, text):
        print(text)
        openai.api_key = self.get_key(self.key)
        try:
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "user",
                        # english prompt here to save tokens
                        "content": f"Please help me to translate,`{text}` to `{self.language}`, please return only translated content not include the origin text unless you can't translate and keep the original markdown format unchanged",
                    }
                ],
            )
            t_text = (
                completion["choices"][0]
                .get("message")
                .get("content")
                .encode("utf8")
                .decode()
            )
            if not NO_LIMIT:
                # for time limit
                time.sleep(3)
        except Exception as e:
            # TIME LIMIT for open api please pay
            key_len = self.key.count(",") + 1
            sleep_time = int(60 / key_len)
            time.sleep(sleep_time)
            print(str(e), "will sleep " + str(sleep_time) + " seconds")
            openai.api_key = self.get_key(self.key)
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "user",
                        "content": f"Please help me to translate,`{text}` to `{self.language}`, please return only translated content not include the origin text unless you can't translate and keep the original markdown format unchanged",
                    }
                ],
            )
            t_text = (
                completion["choices"][0]
                .get("message")
                .get("content")
                .encode("utf8")
                .decode()
            )
        print(t_text)
        return t_text

# 将markdown中的代码块替换为占位符，并将占位符和代码的顺序关系保存到列表中
def extract_code_blocks(md):
    # 用于保存占位符和代码块的顺序关系
    # 匹配markdown代码块
    code_regex = r"\s*```(?:[\w]+)?\n(?:.*\n)*?.*?```"
    # 这里可能会超时 待处理
    code_blocks = re.findall(code_regex, md, re.DOTALL)

    code_dict = {}
    for i, code_block in enumerate(code_blocks):
        placeholder = f"CODE_BLOCK_{i}"
        code_dict[placeholder] = code_block
        md = md.replace(code_block, "\n\n" +placeholder+"\n\n")
    return md, code_dict


def remove_extra_blank_lines(markdown):
    lines = markdown.split('\n')
    result = []
    for i in range(len(lines)):
        if i == 0 or lines[i].strip() or lines[i-1].strip():
            result.append(lines[i])
    return '\n'.join(result)

def check_need_translation(text):
    img_regex = r"!\[[^\]]*\]\((.*?)\)"
    if re.match(img_regex, text):
        return False
    pattern = r"^\W+$"
    if not text.strip() or re.match(pattern, text):
        return False
    return True

def translate_md(md):

    md, code_dict = extract_code_blocks(md)

    print(code_dict)
    print(md)

    paragraphs = md.split("\n\n")

    chatgpt_model = ChatGPT(API_KEY, "english")

    translated_paragraphs = []
    for p in paragraphs:
        pattern = r"\bCODE_BLOCK_\d+\b"
        if re.match(pattern, p):
            translated_paragraphs.append(code_dict[p.strip()])
            continue
        if check_need_translation(p) == False:
            translated_paragraphs.append(p)
            continue

        translation = chatgpt_model.translate(p)
        translated_paragraphs.append(translation)

    translated_text = "\n\n".join(translated_paragraphs)

    translated_text = remove_extra_blank_lines(translated_text)
    print(translated_text)
    return translated_text


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", type=str, help="Input file or URL")
    parser.add_argument("-o", "--output", type=str, help="Output file")
    parser.add_argument("--no_limit",dest="no_limit",action="store_true",help="If you are a paying customer you can add it")
    args = parser.parse_args()
    NO_LIMIT = args.no_limit

    if os.path.isdir(args.input):
        md_files = [f for f in os.listdir(args.input) if f.endswith('.md')]
        for file in md_files:
            print(file)
            with open(os.path.join(args.input, file), 'r') as f:
                md = f.read()
                translated_md = translate_md(md)
                new_filename = os.path.splitext(file)[0] + "_en.md"
                output_path = os.path.join("output", new_filename)  # 设置输出路径
                with open(output_path, 'w') as f:
                    f.write(translated_md)
    else:
        # Read input file or URL
        if args.input.startswith("http"):
            response = requests.get(args.input)
            md = response.text
        else:
            with open(args.input, "r") as f:
                md = f.read()
        # Translate content and output
        translated_md = translate_md(md)
        if args.output:
            output_path = os.path.join("output", args.output)  # 设置输出路径
            with open(output_path, "w") as f:
                f.write(translated_md)
        else:
            print(translated_md)
