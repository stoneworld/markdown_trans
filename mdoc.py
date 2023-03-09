import re
import time
import openai
import requests
import argparse
import os

NO_LIMIT = False
API_KEY = "****"


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
                        "role": "system",
                        # english prompt here to save tokens
                        "content": f"Translate Markdown or YAML to {self.language},If code, only translate comments, please return only translated content not include the origin text unless you can't translate and keep the original markdown or YAML format unchanged",
                    },
                    {
                        "role": "user",
                        # english prompt here to save tokens
                        "content": f"{text}",
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
            sleep_time = int(80 / key_len)
            time.sleep(sleep_time)
            print(str(e), "will sleep " + str(sleep_time) + " seconds")
            openai.api_key = self.get_key(self.key)
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        # english prompt here to save tokens
                        "content": f"Translate Markdown or YAML to {self.language},If code, only translate comments, please return only translated content not include the origin text unless you can't translate and keep the original markdown or YAML format unchanged",
                    },
                    {
                        "role": "user",
                        # english prompt here to save tokens
                        "content": f"{text}",
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


def num_tokens_from_messages(messages):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    num_tokens = len(encoding.encode(messages))

    return num_tokens


def remove_extra_blank_lines(markdown):
    lines = markdown.split('\n')
    result = []
    for i in range(len(lines)):
        if i == 0 or lines[i].strip() or lines[i-1].strip():
            result.append(lines[i])
    return '\n'.join(result)

def group_lines(filename, per_split_num):
    with open(filename, 'r') as f:
        lines = f.readlines()
    i = 0
    code_block_start = 0
    code_block_end = 0
    all_blocks = []
    current_block = []
    while i < len(lines):
        if lines[i].strip().startswith('```'):
            if len(current_block) > 0:
                all_blocks.append("".join(current_block))
                current_block = []
            code_block_start = i
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                i += 1
            code_block_end = i
            current_block = lines[code_block_start:code_block_end+1]
            all_blocks.append("".join(current_block))
            current_block = []
            code_block_end = 0
            code_block_start = 0
            i += 1
        else:
            if len(current_block) > per_split_num:
                all_blocks.append("".join(current_block))
                current_block = []
            current_block.append(lines[i])
            i += 1
    if len(current_block) > 0:
        all_blocks.append("".join(current_block))
    return all_blocks

def translate_md(chatgpt_model, all_blocks):
    translated_paragraphs = []
    for p in all_blocks:
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
    chatgpt_model = ChatGPT(API_KEY, "english")

    if os.path.isdir(args.input):
        md_files = [f for f in os.listdir(args.input) if f.endswith('.md')]
        for file in md_files:
            file_path = os.path.join(args.input, file)
            all_blocks = group_lines(file_path, 10)
            translated_md = translate_md(chatgpt_model, all_blocks)
            new_filename = os.path.splitext(file)[0] + "_translated.md"
            output_path = os.path.join("output", new_filename)  # 设置输出路径
            with open(output_path, 'w') as f:
                f.write(translated_md)
    else:
        file_path = args.input
        all_blocks = group_lines(file_path, 10)
        translated_md = translate_md(chatgpt_model, all_blocks)
        if args.output:
            with open(args.output, "w") as f:
                f.write(translated_md)
        else:
            print(translated_md)
