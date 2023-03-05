import re
import time
import openai
import requests
import argparse

# 将markdown中的代码块替换为占位符，并将占位符和代码的顺序关系保存到列表中
def extract_code_blocks(md):
    # 用于保存占位符和代码块的顺序关系
    # 匹配markdown代码块
    code_regex = r"\s*```(?:[\w]+)?\n(?:.*\n)*?.*?```"
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

def translate_text(text):
    time.sleep(20)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "user",
                # english prompt here to save tokens
                "content": f"Please help me to translate,`{text}` to english, please return only translated content not include the origin text unless you can't translate and keep the original markdown format unchanged",
            }
        ],
    )
    translation = (
        response["choices"][0]
            .get("message")
            .get("content")
            .encode("utf8")
            .decode()
    )
    return translation

openai.api_key = "xxxx"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", type=str, help="Input file or URL")
    parser.add_argument("-o", "--output", type=str, help="Output file")
    args = parser.parse_args()

    # Read input file or URL
    if args.input.startswith("http"):
        response = requests.get(args.input)
        md = response.text
    else:
        with open(args.input, "r") as f:
            md = f.read()

    md, code_dict = extract_code_blocks(md)

    paragraphs = md.split("\n\n")

    translated_paragraphs = []
    for p in paragraphs:
        pattern = r"\bCODE_BLOCK_\d+\b"
        matches = re.findall(pattern, p)
        if re.match(pattern, p):
            translated_paragraphs.append(code_dict[p.strip()])
            continue
        if check_need_translation(p) == False:
            translated_paragraphs.append(p)
            continue

        translation = translate_text(p)
        translated_paragraphs.append(translation)

    translated_text = "\n\n".join(translated_paragraphs)

    translated_text = remove_extra_blank_lines(translated_text)

    if args.output:
        with open(args.output, "w") as f:
            f.write(translated_text)
    else:
        print(translated_text)