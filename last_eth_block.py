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
            return result
    return result


# average reward on the last 100 block
def get_average_reward(blocks):
    return sum(block['reward'] for block in blocks)/len(blocks)


# write last 100 block to json file
def dump_file(blocks):
    with open('blocks.json', 'w', encoding='utf-8') as file:
        json.dump(blocks, file, indent=4, ensure_ascii=False)


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


def test():
    # html = get_html('https://etherscan.io/blocks?ps=100')
    # with open('index.html', 'w', encoding='utf-8') as file:
    #     file.write(html)
    with open('index.html', 'r', encoding='utf-8') as file:
        html = file.read()
    new_blocks = get_new_block_list(html)
    with open('blocks.json', 'w', encoding='utf-8') as file:
        json.dump(new_blocks, file, indent=4, ensure_ascii=False)
    with open('blocks.json', 'r', encoding='utf-8') as file:
        new_blocks = json.load(file)[0:200]
    print(len(new_blocks))


def main():
    # last 100 blocks
    all_block = []

    while True:
        # get last 100 blocks
        html = get_html('https://etherscan.io/blocks?ps=100')
        # get new blocks
        min_id = all_block[0].get('id') if all_block else 0
        new_blocks = get_new_block_list(html, min_id)

        # if new_block found
        if new_blocks:
            print(f"{time.strftime('%H:%M:%S %d-%m-%Y', time.gmtime())} Found {len(new_blocks)} new block. ID:",
                  [block_id['id'] for block_id in new_blocks])
            all_block.extend(new_blocks)
            all_block.sort(key=lambda x: x['id'], reverse=True)
            all_block = all_block[:100]
            # save in file
            dump_file(all_block)
            # calc new average reward
            average_reward = get_average_reward(all_block)

            for new_block in new_blocks:
                if new_block['reward'] > average_reward * MAX_COEF:
                    print(f"Block with big reward {new_block}")

            print_popular_miner(all_block)

        time.sleep(random.randint(30, 60))


if __name__ == '__main__':
    # test()
    main()
