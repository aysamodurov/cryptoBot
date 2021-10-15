from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text
from config import TELEGRAM_TOKEN
from last_eth_block import get_html, get_new_block_list, get_average_reward, print_popular_miner, get_best_miner, update_pool_stat
from crypto_market import get_current_btc_usd, get_current_eth_usd
import json
import asyncio
import time
import random
import collections

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)
with open('subscribers.json', 'r', encoding='utf-8') as file:
    try:
        subscribers = json.load(file)
    except Exception as ex:
        subscribers = []
        print('Error to open file subscribers.json')

# Кнопки
start_buttons = ['Управление подпиской', 'Топ пулов', 'Курсы криптовалют']
subscriber_buttons = ['Подписаться на рассылку', 'Отменить подписку', 'Статус подписки', 'Назад']
crypto_market_button = ['ETH/USD', 'BTC/USD', 'Назад']


@dp.message_handler(commands='start')
async def start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*start_buttons)

    await message.answer(f"Привет {message.from_user.first_name}, я бот который помогает отслеживать "
                         f"аномальные всплески в комиссиях сети ETHERIUM", reply_markup=keyboard)


# МЕНЮ ПОДПИСКА
# подписаться
@dp.message_handler(Text(equals=subscriber_buttons[0]))
async def subscripe(message: types.Message):
    user_id = message.from_user.id
    if user_id in subscribers:
        await message.answer("Вы уже подписаны")
    else:
        subscribers.append(message.from_user.id)
        update_subscribers(subscribers)
        await message.answer("Вы подписались на уведомления")


# отменить подписку
@dp.message_handler(Text(equals=subscriber_buttons[1]))
async def unsubscripe(message: types.Message):
    if message.from_user.id not in subscribers:
        await message.answer(f'Вы не подписаны')
    else:
        await message.answer(f"Подписка отменена")
        subscribers.remove(message.from_user.id)
        update_subscribers(subscribers)


# статус подписки
@dp.message_handler(Text(equals=subscriber_buttons[2]))
async def subscripe_status(message: types.Message):
    user_id = message.from_user.id
    if user_id in subscribers:
        await message.answer('Подписка активна')
    else:
        await message.answer('Подписка не активна')
# КОНЕЦ МЕНЮ ПОДПИСКА


# МЕНЮ КУРСЫ криптовалют
@dp.message_handler(Text(equals=crypto_market_button[0]))
async def subscripe(message: types.Message):
    """Click to coin matket ETH
    :param message:
    :return: print marker price ETH
    """
    eth_usd = get_current_eth_usd()
    await message.answer(f"*1 ETH = {eth_usd} USD*", parse_mode="Markdown")


# отменить подписку
@dp.message_handler(Text(equals=crypto_market_button[1]))
async def unsubscripe(message: types.Message):
    """
    Click to coin matket BTC
    :param message:
    :return: print marker price BTC
    """
    btc_usd = get_current_btc_usd()
    await message.answer(f"*1 BTC = {btc_usd} USD*", parse_mode="Markdown")
# КОНЕЦ МЕНЮ КУРСЫ КРИПТОВАЛЮТ


# назад общая кнопка дя возвращения в главное меню
@dp.message_handler(Text(equals=subscriber_buttons[3]))
async def back_click(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*start_buttons)
    await message.answer('Главное меню', reply_markup=keyboard)


# ГЛАВНОЕ МЕНЮ
# Топ пулов
@dp.message_handler(Text(equals=start_buttons[0]))
async def get_subscribe_menu(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*subscriber_buttons)
    await message.answer('Управление подпиской', reply_markup=keyboard)


# Топ пулов
@dp.message_handler(Text(equals=start_buttons[1]))
async def get_best_miners(message: types.Message):
    best_miners = get_best_miner()
    resstr = ''
    for miner in best_miners:
        resstr = resstr + miner + '\n'
    await message.answer(resstr)


# курсы криптовалют
@dp.message_handler(Text(equals=start_buttons[2]))
async def get_eth_usd(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*crypto_market_button)
    await message.answer('Курсы криптовалют', reply_markup=keyboard)
# КОНЕЦ ГЛАВНОГО МЕНЮ


async def send_message_all_subscribers(text):
    for subsc in subscribers:
        await bot.send_message(subsc, text)


async def update_blocks():
    # last  blocks
    ANOMAL_COEF = 1.8
    COUNT_BLOCK = 200
    all_block = collections.deque(maxlen=COUNT_BLOCK)
    while True:
        # get last 100 blocks
        html = get_html('https://etherscan.io/blocks?ps=100')

        # get new blocks
        min_id = all_block[-1].get('id') if all_block else 0
        new_blocks = get_new_block_list(html, min_id)

        # if new_block found
        if new_blocks:
            print(f"{time.strftime('%H:%M:%S %d-%m-%Y', time.gmtime())} Found {len(new_blocks)} new block. ID:",
                  [block_id['id'] for block_id in new_blocks])
            # update poolstatistic
            update_pool_stat(new_blocks)

            # update last found block
            for block in new_blocks:
                all_block.append(block)

            print(f"In memory store last {len(all_block)} blocks")
            # calc new average reward
            average_reward = get_average_reward(all_block)

            # сохранить самые пулы (майнеры) с наибольшим количеством шар за последние COUNT_BLOCK блоков
            print_popular_miner(all_block)

            for new_block in new_blocks:
                if new_block['reward'] > average_reward * ANOMAL_COEF:
                    await send_message_all_subscribers(u'\U00002757\U00002757\U00002757'+f" Блок ID - {new_block['id']}, время {new_block['time']} "
                                                       f"имеет большое вознаграждение {new_block['reward']}, miner: {new_block['miner']}")
        await asyncio.sleep(random.randint(10, 20))


# обновление списка подписчиков в файле json
def update_subscribers(subscribers):
    with open('subscribers.json', 'w', encoding='utf-8') as file:
        json.dump(subscribers, file, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(update_blocks())
    executor.start_polling(dp)
