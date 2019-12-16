import os
import telegram
from telegram.ext import Updater, CommandHandler
import logging
from urllib.request import urlretrieve
from bs4 import BeautifulSoup

token = os.getenv('TG_TOKEN')
if not token:
    raise Exception("Token env var undefined")
bot = telegram.Bot(token=token)
updater = Updater(token=token, use_context=True)
dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


def get_data():
    # prep data
    hot_game_data = os.path.join(os.getcwd(), 'nba_data.php')
    urlretrieve("http://stats.inpredictable.com/nba/preCap.php", hot_game_data)

    with open(hot_game_data) as f:
        content = f.read()
    soup = BeautifulSoup(content, 'html.parser')
    table = soup.find(class_="iptbl").find("tbody")
    scores_headers = [head.get_text() for head in table.findAll('th')]
    scores_table = table.findAll('tr')
    scores_dict = dict()
    for score in scores_table[1:]:
        game = score.find("td").get_text()
        scores_dict[game] = dict.fromkeys(scores_headers)
        values = score.findAll("td")
        for i, header in enumerate(scores_dict[game]):
            scores_dict[game][header] = values[i].get_text()

    return scores_dict


def present_hot_games():
    data = get_data()
    text = f"The best game for today is {data['1']['Game']} with a {data['1']['Excitement']} Excitement level \n"
    text += f"All other games excitement level: \n"
    for i in range(2, len(data)+1):
        text += f"{data[str(i)]['Game']} - {data[str(i)]['Excitement']}\n"

    return text


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=present_hot_games())


print(present_hot_games())
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)
updater.start_polling()

