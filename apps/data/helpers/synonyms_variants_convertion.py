import os
import json
import itertools 

def load_mappings(*args, **kwargs):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, 'mappings.json')
    
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def replace_synonyms(input_str, synonyms):
    """
    功能：
    將輸入的字串逐字切割，遇到同義詞時替換成完整字

    參數：
    input_str: 使用者輸入的字串
    synonyms: 同義詞對照表

    回傳：
    替換後的字串
    """

    # result = []
    # i = 0
    # while i < len(input_str):
    #     replaced = False
    #     # 匹配長度從2開始的詞組，直到整個字串
    #     for length in range(2, len(input_str) - i + 1):
    #         print(length, i)
    #         word = input_str[i:i + length]
    #         print(f'word: {word}')
    #         if word in synonyms:
    #             result.append(synonyms[word])  # 替換為同義詞
    #             i += length  # 跳過已替換的詞組
    #             replaced = True
    #             break
    #     # 如果沒有匹配，則保留當前字元
    #     if not replaced:
    #         result.append(input_str[i])
    #         i += 1
    # return ''.join(result)
    result = []
    i = 0
    while i < len(input_str) - 1:  # 確保可以取到兩個字
        word = input_str[i:i + 2]  # 取兩個字
        if word in synonyms:
            result.append(synonyms[word])  # 替換為同義詞
            i += 2  # 跳過已替換的兩個字
        else:
            result.append(input_str[i])  # 保留當前字
            i += 1  # 只處理一個字
    # 若最後一個字沒有被處理（當字串長度為奇數時），將其添加到結果中
    if i < len(input_str):
        result.append(input_str[i])
    return ''.join(result)


def generate_variants(input_str, variant_map):
    """
    功能：
    根據異體字映射表生成所有可能的異體字組合

    參數：
    input_str: 使用者輸入的字串
    variant_map: 異體字對照表

    回傳：
    異體字組合列表
    """
    
    # 逐一將字替換成異體字列表
    char_variants = [
        [char] + ([variant_map[char]] if char in variant_map else [])
        for char in input_str
    ]
    
    # 對 char_variants 的每個子列表進行笛卡兒積計算，產生所有可能的字元排列組合
    return [''.join(combo) for combo in itertools.product(*char_variants)]