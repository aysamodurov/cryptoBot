import requests
from bs4 import BeautifulSoup
import json
import time
import random
from collections import Counter

MAX_COEF = 1.5


def get_html(url):
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/93.0.4577.63 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,'
                  'image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
    }
    try:
        response = requests.get(url=url, headers=headers)
    except Exception as ex:
        print("Ошибка при подключении к ", url)
        print(ex)
        return None
    with open('last_index.html', 'w', encoding='utf-8') as file:
        file.write(response.text)
    if response.status_code == 200:
        return response.text
    else:
        print('Ошибка доступа к сайту', url)
        return None


# get blocks list from html with id mare then min_id
def get_new_block_list(html, min_id=0):
    if not html:
        return None
    soup = BeautifulSoup(html, 'lxml')
    find_blocks = soup.find('div', class_='table-responsive').find('tbody').find_all('tr')
    result = []
    for find_block in find_blocks:
        find_block_record = find_block.find_all('td')
        block_id = int(find_block_record[0].text.strip())
        if block_id > min_id:
            block_time = find_block_record[1].text.strip()
            block_miner = find_block_record[5].text.strip()
            block_reward = float(find_block_record[9].text.split(' ')[0].strip())
            block_burnt_fees = float(find_block_record[10].text.split(' ')[0].strip())
            block = {
                'id': block_id,
                'time': block_time,
                'miner': block_miner,
                'reward': block_reward,
                'burnt_fees': block_burnt_fees
            }
            result.append(block)
        else:
            return sorted(result,key=lambda k:k['id'])
    return sorted(result,key=lambda k:k['id'])


# average reward on the last 100 block
def get_average_reward(blocks):
    return sum(block['reward'] for block in blocks)/len(blocks)


# get best pool(miner)
def get_best_miner():
    with open('miners.txt', 'r', encoding='utf-8') as file:
        return file.readlines()


# get most popular miner
def print_popular_miner(blocks):
    counter = Counter([item['miner'] for item in blocks])
    counter = counter.most_common()
    with open('miners.txt', 'w', encoding='utf-8') as file:
        file.write(f"{'MINER'}   :   COUNT SHARE\n")
        for key, val in counter:
            file.write(f"{key}   :   {val}\n")

def update_pool_stat(blocks):
    """Update find share on pool

    :param block: list of new ETH block
    :return:
    """
    # read pool statistic from file out\pool_stat.json
    import json
    import os
    # check exist folder out an file pool_stat.json
    if not os.path.exists('out'):
        os.mkdir('out')
    if not os.path.exists('out\\pool_stat.json'):
        counter_old = Counter()
    else:
        with open('out\\pool_stat.json', 'r', encoding='utf-8') as json_file:
            try:
                counter_old = Counter(json.load(json_file))
            except Exception as ex:
                print(f'{ex}, file pool_stat.json is empty, create new pool statistic')
                counter_old = Counter()

    # get new pool shares
    counter = Counter([item['miner'] for item in blocks])
    counter = counter + counter_old
    with open('out\\pool_stat.json', 'w', encoding='utf-8') as json_file:
        json.dump(counter, json_file,indent=4,ensure_ascii=False)
