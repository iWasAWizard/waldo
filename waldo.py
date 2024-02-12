import sys
import re
import unicodedata
import itertools


def get_strings(text):
    chars = r"A-Za-z0-9/\-:.,_$%'()[\]<> "
    shortest_string = 4

    expression = '[%s]{%d,}' % (chars, shortest_string)
    pattern = re.compile(expression)

    return pattern.findall(text)


def remove_unprintable_chars(text):
    all_chars = (chr(i) for i in range(sys.maxunicode))
    categories = {'Cc'}
    control_chars = ''.join(map(chr, itertools.chain(range(0x00, 0x20), range(0x7f, 0xa0))))

    control_char_re = re.compile('[%s]' % re.escape(control_chars))

    return control_char_re.sub('', text)


if __name__ == '__main__':
    all_str = []

    with open(sys.argv[1], 'r', errors='surrogateescape') as target:
    
        clean_text = remove_unprintable_chars(target.read())
    
    with open('all_found_strings.txt', 'w') as all_strings:    
        for found in get_strings(clean_text):
            all_strings.write(found + '\n')
            all_str.append(found)
                

    if sys.argv[2]:
        with open(sys.argv[2], 'r') as word_list:
            with open('filtered_strings.txt', 'w') as filtered_strings:
                for word in word_list:

                    pattern = re.compile(f'(?i){word.strip()}')

                    for string in all_str:
                        res = pattern.match(string)
                              
                        if res:
                            filtered_strings.write(string + ' : ' + word + '\n')
