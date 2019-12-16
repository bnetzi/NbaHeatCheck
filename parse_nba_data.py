import os

from nba_pbp_scraper import nba_pbp_scraper
from datetime import datetime, timedelta
from main import get_data
import numpy as np
import pandas as pd

def get_games():
    today = (datetime.today()- timedelta(days=1)).strftime('%Y%m%d')
    games = get_data()

    for i in range(2, len(games)+1):
        game_title = games[str(i)]['Game']
        teams = game_title.split()
        try:
            df = pd.read_pickle(os.getcwd() + game_title + today)
        except Exception as FileNotFoundError:
            df = nba_pbp_scraper.pbp_to_df(teams[0], teams[2], today)
            df.to_pickle(os.getcwd() + game_title + today)

        last_index = df['Time'].last_valid_index()
        last_move = df[df['Event_num'] == last_index]
        final_aw_score, curr_aw_score = last_move.Aw_Score
        final_hm_score, curr_hm_score = last_move.Hm_Score
        last_home_leads, curr_hm_leads = final_hm_score > final_aw_score

        is_very_close = False
        is_close = False
        lead_changes = 0
        is_last_minute = true
        is_last_5 = true

        # Itreate over last 5 minutes move and check if game is close
        for i in range(last_index, 0, -1):
            curr_move = df[df['Event_num'] == i]
            curr_aw_score, curr_hm_score = curr_move.Aw_Score, curr_move.Hm_score
            minutes_left = curr_move.Time.values[0].split(":")[0]
            is_last_minute = minutes_left < '1'
            is_last_5 = minutes_left < '5'
            curr_home_leads = curr_hm_score > curr_aw_score
            if curr_hm_leads != last_home_leads:
                lead_changes += 1
            last_home_leads = curr_hm_leads
            if not is_last_5:
                break
            if is_last_minute:
                if lead_changes > 1 or abs(curr_aw_score - curr_hm_score) <= 3:
                    is_very_close = True
                    break
                if abs(curr_aw_score - curr_hm_score) <= 5:
                    is_close = True
            if is_last_5:
                if lead_changes > 5:
                    is_very_close = True
                    break
                if lead_changes > 1:
                    is_close = True

        games[str(i)]['How-close'] = 'Very close' if is_very_close else 'Close' if is_close else None
    return games
