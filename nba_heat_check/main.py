import os
import telegram
from telegram.ext import Updater, CommandHandler
import logging
from urllib.request import urlretrieve
from bs4 import BeautifulSoup
from nba_pbp_scraper import nba_pbp_scraper
from datetime import datetime, timedelta
import pandas as pd


def get_data():
    # prep data
    hot_game_data = os.path.join(os.getcwd(), 'nba_data.php')
    urlretrieve("http://stats.inpredictable.com/nba/preCap.php", hot_game_data)

    with open(hot_game_data) as f:
        content = f.read()
    soup = BeautifulSoup(content, 'html.parser')
    table = soup.find(class_="iptbl").find("tbody")
    scores_headers = [head.get_text() for head in table.findAll('th')]
    unimportant_headers_index = scores_headers.index('League Averages')
    scores_headers = scores_headers[:unimportant_headers_index]
    scores_table = table.findAll('tr')
    scores_dict = dict()
    for score in scores_table[1:-1]:
        game = score.find("td").get_text()
        scores_dict[game] = dict.fromkeys(scores_headers)
        values = score.findAll("td")
        for i, header in enumerate(scores_dict[game]):
            scores_dict[game][header] = values[i].get_text()

    return scores_dict


def get_games():
    today = (datetime.today() - timedelta(days=1)).strftime('%Y%m%d')
    games = get_data()

    for game_index in range(2, len(games)+1):
        game_title = games[str(game_index)]['Game']
        teams = game_title.split()
        file_path = os.getcwd() + game_title + today
        if os.path.isfile(file_path):
            df = pd.read_pickle(file_path)
        else:
            try:
                df = nba_pbp_scraper.pbp_to_df(teams[0], teams[2], today)
                df.to_pickle(file_path)
            except Exception as e:
                print("pbp package failed with" + str(e.args))
                continue

        last_index = df['Time'].last_valid_index()
        last_move = df[df['Event_num'] == last_index]
        final_aw_score = curr_aw_score = last_move.Aw_Score
        final_hm_score = curr_hm_score = last_move.Hm_Score
        last_home_leads = curr_hm_leads = final_hm_score > final_aw_score

        is_very_close = False
        is_close = False
        lead_changes = 0

        # Iterate over last 5 minutes move and check if game is close
        for i in range(last_index, 0, -1):
            curr_move = df[df['Event_num'] == i]
            curr_aw_score, curr_hm_score = curr_move.Aw_Score, curr_move.Hm_Score
            minutes_left = curr_move.Time.values[0].split(":")[0]
            is_last_minute = minutes_left < '1'
            is_last_5 = minutes_left < '5'
            curr_hm_leads = curr_hm_score > curr_aw_score
            if curr_hm_leads.bool() != last_home_leads.bool():
                lead_changes += 1
            last_home_leads = curr_hm_leads
            if not is_last_5:
                break
            if is_last_minute:
                if lead_changes > 1 or int(abs(curr_aw_score - curr_hm_score)) <= 3:
                    is_very_close = True
                    break
                if int(abs(curr_aw_score - curr_hm_score)) <= 5:
                    is_close = True
            if is_last_5:
                if lead_changes > 5:
                    is_very_close = True
                    break
                if lead_changes > 1:
                    is_close = True

        games[str(game_index)]['How-close'] = 'Very close game' if is_very_close else 'Close game' if is_close else None

    return games


def present_hot_games():
    data = get_games()
    text = f"All Games Interest level:\n"
    for i in range(1, len(data)+1):
        text += f"{data[str(i)]['Game']} - {data[str(i)]['Excitement']}"
        text += f" - {data[str(i)]['How-close']}\n" if data[str(i)].get('How-close') else f"\n"

    print(text)
    return text


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Processing Data")
    context.bot.send_message(chat_id=update.effective_chat.id, text=present_hot_games())


def run(updater):
    if os.getenv('MODE') == 'prod':
        port = int(os.environ.get("PORT", "8443"))
        heroku_app_name = "nbaheatcheck"
        updater.start_webhook(listen="0.0.0.0",
                              port=port,
                              url_path=Token)
        updater.bot.set_webhook("https://{}.herokuapp.com/{}".format(heroku_app_name, Token))
    else:
        updater.start_polling()


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger()

    # Get Telegram Token
    Token = os.getenv('TG_TOKEN')
    if not Token:
        raise Exception("Token env var undefined")

    # Init bot and add handlers
    bot = telegram.Bot(token=Token)
    updater = Updater(token=Token, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', start))

    run(updater)

