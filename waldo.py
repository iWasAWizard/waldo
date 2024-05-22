#!/usr/bin/python3
"""Dirty word search"""

import os
import re
from typing import Optional, List, Tuple

IGNORE: List[str] = ["git", "test", "svg", "cache"]


# pylint: disable=missing-function-docstring
def get_file_list(target_path: Optional[str] = None) -> List[str]:
    """Returns recursive list of files in ``target_path``"""
    if target_path is None:
        dir_list = [os.path.abspath(os.path.join(os.getcwd(), os.pardir))]
    else:
        dir_list = [target_path]

    file_list: List[str] = []
    removed_files: List[str] = []

    # BEGIN BLACK MAGIC
    while len(dir_list) > 0:
        for (dir_path, dir_names, file_names) in os.walk(dir_list.pop()):
            dir_list.extend(dir_names)
            file_list.extend(map(lambda n: os.path.join(*n),
                                 zip([dir_path] * len(file_names),
                                     file_names)))

    for file in file_list:
        for item in IGNORE:
            if item in file:
                removed_files.append(file)

    for file in removed_files:
        if file in file_list:
            file_list.remove(file)

    print(f"[*] File search complete! Got {len(file_list)} files to check!")

    with open("./dws_removed.txt", "w", encoding="utf-8") as ignored:
        for item in removed_files:
            ignored.write(str(item))

    return file_list


MatchList = List[Tuple[str, str, str]]

# pylint: disable=missing-function-docstring
def dirty_word_search(dirty_word_list: str, file_list: List[str]) -> MatchList:
    """Performs a dirty word search, returning list of files with dirty words"""
    dirty_files: MatchList = []

    # Iterate over dirty words, then over target files
    with open(dirty_word_list, "r", encoding="utf-8") as dirty_words:
        for word in dirty_words:
            regexp: re.Pattern = re.compile(word.rstrip())
            regexp_bytes: re.Pattern = re.compile(bytes(word.rstrip(), "utf-8"))
            line_number = 0
            match: Optional[re.Match]
            for filename in file_list:
                print(f"[*] Searching {filename}...")
                try:
                    with open(filename, "r", encoding="utf-8") as target:
                        for line in target:
                            line_number += 1
                            match = re.search(regexp, line)
                            if match:
                                if match == "\n":
                                    pass
                                print(f"[*] HIT! File: \
                                        {filename} Line: {line_number}")

                                match_content = (filename,
                                                 word.rstrip(),
                                                 str(line_number))
                except FileNotFoundError:
                    pass

                except UnicodeError:
                    # Unicode failed so this must be a binary file
                    chunk = b""
                    # Chunk size is arbitrary, could be sped up.
                    chunk_size = 4096
                    with open(filename, "rb", encoding=None) as target:
                        if chunk_size > 4096:
                            chunk = chunk[chunk_size:]
                        chunk += target.read(chunk_size)
                        match = re.search(regexp_bytes, chunk)
                        if match is not None:
                            print(f"[*] HIT! File: \
                                {filename} Offset {match.start()}")

                            match_content = (filename,
                                             word.rstrip(),
                                             f"offset={match.start()}")

                except PermissionError:
                    # Hope there's nothing in there
                    pass

                if match:
                    match_content = (filename, word.rstrip(), str(line_number))
                    dirty_files.append(match_content)

    return dirty_files


# pylint: disable=missing-function-docstring
def output(match_list: MatchList, output_path: Optional[str] = None):
    """Writes list of files to file ``output_path``"""
    if output_path is None:
        output_path = "./dws_results.txt"

    with open(output_path, "w", encoding="utf-8") as file:
        for match in match_list:
            file.writelines(f"{match}\n")


if __name__ == '__main__':
    res = get_file_list()
    matches = dirty_word_search("./dirtywordlist.txt", res)
    output(match_list=matches)
