import os
import fnmatch
import shutil



def copy_md_files(source_dir, dest_dir):
    md_files = []
    # 遍历 source_dir 目录及其子目录下的所有文件和文件夹
    for root, dirs, files in os.walk(source_dir):
        # 遍历所有文件
        for filename in files:
            if filename.endswith('.md'):
                # 获取前两级目录名作为文件名前缀
                first_level_dir = os.path.basename(os.path.dirname(root))
                second_level_dir = os.path.basename(root)
                prefix = first_level_dir + '_' + second_level_dir
                # 复制和重命名文件
                name, ext = os.path.splitext(filename)
                new_filename = prefix + '_' + name + '_cn' + ext
                src_path = os.path.join(root, filename)
                dst_path = os.path.join(dest_dir, new_filename)
                shutil.copy2(src_path, dst_path)
                md_files.append(dst_path)
    return md_files
