import os
import shutil
import warnings
import zipfile
import tarfile
import rarfile
import py7zr
import logging
from tqdm import tqdm
import textwrap

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def print_intro():
    intro_text = r"""
 ______       _   _            _
|__  (_)_ __ | | | | __ _  ___| | _____ _ __ 
  / /| | '_ \| |_| |/ _` |/ __| |/ / _ \ '__|
 / /_| | |_) |  _  | (_| | (__|   <  __/ |   
/____|_| .__/|_| |_|\__,_|\___|_|\_\___|_|   
       |_|
"""

    author_text = "Author: Loong"
    blog_text = "Blog: https://gitee.com/yangyilong2004"

    print("\n" + intro_text)
    print(textwrap.fill(author_text, width=70))
    print(textwrap.fill(blog_text, width=70))
    print("\n" + "-" * 70 + "\n")


def is_zip_fake_encrypted(file_path):
    """
    检查zip文件是否存在伪加密
    """
    with zipfile.ZipFile(file_path) as zf:
        for info in zf.infolist():
            if info.flag_bits & 0x1:
                return True
    return False

def fix_zip_encrypted(file_path):
    """
    修复伪加密的zip文件
    """
    temp_path = file_path + ".tmp"
    with zipfile.ZipFile(file_path) as zf, zipfile.ZipFile(temp_path, "w") as temp_zf:
        for info in zf.infolist():
            if info.flag_bits & 0x1:
                info.flag_bits ^= 0x1  # 清除加密标记
            temp_zf.writestr(info, zf.read(info.filename))
    fix_zip_name = "fix_" + file_path
    try:
        shutil.move(temp_path, fix_zip_name)
    except Exception as e:
        os.remove(fix_zip_name)
        shutil.move(temp_path, fix_zip_name)
        logging.error(f"修复伪加密文件时出错: {e}", exc_info=True)
    return fix_zip_name

def extract_zip(file_path, target_dir):
    try:
        # 检查并处理伪加密的ZIP文件
        if is_zip_fake_encrypted(file_path):
            logging.warning(f"{file_path} 是伪加密的文件，尝试修复...")
            file_path = fix_zip_encrypted(file_path)
            logging.info(f"修复完成，生成新文件: {file_path}")

        with zipfile.ZipFile(file_path, 'r') as zip_file:
            zip_file.extractall(path=target_dir)
    except Exception as e:
        logging.error(f"解压 .zip 文件失败: {file_path}, 错误: {e}", exc_info=True)

def extract_tar(file_path, target_dir):
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            with tarfile.open(file_path, 'r:*') as tar_file:
                tar_file.extractall(path=target_dir)
    except Exception as e:
        logging.error(f"解压 .tar 文件失败: {file_path}, 错误: {e}", exc_info=True)

def extract_rar(file_path, target_dir):
    try:
        with rarfile.RarFile(file_path, 'r') as rar_file:
            rar_file.extractall(path=target_dir)
    except Exception as e:
        logging.error(f"解压 .rar 文件失败: {file_path}, 错误: {e}", exc_info=True)

def extract_7z(file_path, target_dir):
    try:
        with py7zr.SevenZipFile(file_path, 'r') as seven_z_file:
            seven_z_file.extractall(path=target_dir)
    except Exception as e:
        logging.error(f"解压 .7z 文件失败: {file_path}, 错误: {e}", exc_info=True)

def extract_file(file_path, target_dir):
    """ 根据文件类型解压文件 """
    if zipfile.is_zipfile(file_path):
        extract_zip(file_path, target_dir)
    elif tarfile.is_tarfile(file_path):
        extract_tar(file_path, target_dir)
    elif rarfile.is_rarfile(file_path):
        extract_rar(file_path, target_dir)
    elif py7zr.is_7zfile(file_path):
        extract_7z(file_path, target_dir)
    else:
        logging.warning(f"无法处理的文件类型: {file_path}")
        return False
    return True

def process_file(file_path, target_dir, del_file):
    """
    处理文件解压并递归处理嵌套压缩文件
    """
    success = extract_file(file_path, target_dir)

    if success and del_file.upper() == 'Y':
        try:
            os.remove(file_path)
            logging.info(f"成功删除原文件: {file_path}")
        except Exception as e:
            logging.error(f"删除文件失败: {file_path}, 错误: {e}", exc_info=True)

    return success

def decompression(dirname, del_file='N'):
    count = 0
    print_intro()  # 打印工具信息

    while True:
        file_list = []
        
        # 遍历目录并找到所有压缩文件
        for root, _, files in os.walk(dirname):
            for file in files:
                file_path = os.path.join(root, file)
                if zipfile.is_zipfile(file_path) or tarfile.is_tarfile(file_path) or rarfile.is_rarfile(file_path) or py7zr.is_7zfile(file_path):
                    file_list.append(file_path)
        
        # 如果没有更多压缩文件，结束循环
        if not file_list:
            break

        for file_path in tqdm(file_list, desc="解压文件进度", unit="file", mininterval=1.0):
            if process_file(file_path, dirname, del_file):
                count += 1
                # 输出当前进度和成功解压的文件数量
                logging.info(f"成功解压文件: {file_path}")
            else:
                logging.error(f"处理文件失败: {file_path}")

    logging.info(f"解压完成，共解压文件 {count} 个")

# 示例调用
try:
    decompression(r'C:\Users\leeso\Desktop\demo', 'Y')  # 修改路径以适合你的情况，Y表示删除原压缩文件
except Exception as error:
    logging.error(f"An error occurred: {error}", exc_info=True)
