import json
import datetime
import random
import re
import os


# ディレクトリ
JSON_DIR = 'json'
TWEET_STATUS_FILE = 'tweet_status.txt'
re_kanji = re.compile(r'^[\u4E00-\u9FD0]+$')
characters={}

# 感じを取得して辞書式に入れてくれる関数
def get_chara(text):
    for chara in text:
        if re_kanji.fullmatch(chara):
            # 辞書にあるかどうかで分岐
            if chara in characters:
                characters[chara] += 1
            else:
                characters[chara] = 1

# jsonにぶち込む
def save_json(dict):
    now = datetime.datetime.now()
    total_json = os.path.join(JSON_DIR, 'total.json')
    daily_json = os.path.join(JSON_DIR, '{0:%Y%m%d}.json'.format(now-datetime.timedelta(hours=3)))

    # トータル
    with open(total_json, 'r', encoding='utf-8') as f:
        saved_charas = json.load(f)
        for chara in characters:
            # 中にあるか
            if characters[chara] in saved_charas:
                saved_charas[chara] += characters[chara]
            else:
                saved_charas[chara] = characters[chara]

        if (0 <= now.hour <= 1) and (0 <= now.minute <= 15):
            print(saved_charas)

    # 書き込み
    with open(total_json, 'w', encoding='utf-8') as f:
        json.dump(saved_charas, f)

    # デイリーヤマザキなほう
    if not os.path.exists(daily_json):
        with open(daily_json, 'a', encoding='utf-8') as f:
            d = {}
            json.dump(d, f)

    with open(daily_json, 'r', encoding='utf-8') as f:
        saved_charas = json.load(f)
        for chara in characters:
            # 中にあるか
            if characters[chara] in saved_charas:
                saved_charas[chara] += characters[chara]
            else:
                saved_charas[chara] = characters[chara]

    # 書き込み
    with open(daily_json, 'w', encoding='utf-8') as f:
        json.dump(saved_charas, f)

# ランキング
def ranking():
    now = datetime.datetime.now()
    total_json = os.path.join(JSON_DIR, 'total.json')
    daily_json = os.path.join(JSON_DIR, '{0:%Y%m%d}.json'.format(now-datetime.timedelta(hours=3)))

    with open(daily_json, 'r', encoding='utf-8') as f:
        daily_rank = sorted(json.load(f).items(), key=lambda x:x[1], reverse=True)[0:3]
        random_chara = random.choice(daily_rank)

    with open(total_json, 'r', encoding='utf-8') as f:
        total_rank = sorted(json.load(f).items(), key=lambda x:x[1], reverse=True)[0:3]

    return [daily_rank, total_rank, random_chara]



# --------------------------------------------------------------------------
import tweepy
from flask import Flask

# 例のあれ
app = Flask(__name__)

@app.route('/')
def tweet():
    # app作成
    # キーとか
    CONSUMER_KEY = os.environ['CONSUMER_KEY']
    CONSUMER_SECRET = os.environ['CONSUMER_SECRET']
    ACCESS_TOKEN = os.environ['ACCESS_TOKEN']
    ACCESS_TOKEN_SECRET = os.environ['ACCESS_TOKEN_SECRET']

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth, wait_on_rate_limit=True)
    me = api.me()

    # 禁句
    banned_words = 'ネットビジネス|副業'

    # 日付類
    now = datetime.datetime.now()
    since = now - datetime.timedelta(hours=9, minutes=15)

    # プリンと
    print('--- [{0}]'.format(now))

    # ツイート収集機構
    for status in tweepy.Cursor(api.home_timeline, exclude_replies=True, exclude_retweets=True, lang='ja', since=since).items(count=250):
        if (status.created_at - since).total_seconds() < 0:
            break

        else:
            get_chara(status.text)
            print('Got tweet made by @{1} at [{0}].'.format(status.created_at+datetime.timedelta(hours=9), status.id))

    save_json(characters)

    # ツイートする機構
    with open(TWEET_STATUS_FILE, 'r', encoding='utf-8') as f:
        isTweeted = f.readline()

    if (now.hour % 12 == 9) and (re.search(r'False', isTweeted)):
        with open(TWEET_STATUS_FILE, 'w', encoding='utf-8') as f:
            try:
                ranks = ranking()
                tweet = '[今日TLで使われた漢字ランキング！]\n1位:『{0}』--{1}回\n2位:『{2}』--{3}回\n3位:『{4}』--{5}回\n\n[これまでTLで使われた漢字ランキング！]\n1位:『{6}』--{7}回\n2位:『{8}』--{9}回\n3位:『{10}』--{11}回\n\nそんな今日を一文字で表すと...\n＿人人人人＿\n＞　『{12}』　＜\n￣Y^Y^Y^Y￣'.format(ranks[0][0][0], ranks[0][0][1], ranks[0][1][0], ranks[0][1][1], ranks[0][2][0], ranks[0][2][1], ranks[1][0][0], ranks[1][0][1], ranks[1][1][0], ranks[1][1][1], ranks[1][2][0], ranks[1][2][1], ranks[2][0])
                api.update_status(tweet)
                print('Succeed in posting a tweet.')
            except:
                print('Failed to post a tweet.')

            f.write('True')

    elif (now.hour % 12 == 8) and (re.search(r'True', isTweeted)):
        with open(TWEET_STATUS_FILE, 'w', encoding='utf-8') as f:
            f.write('False')
            print('Tweet status has been reset.')

    else:
        print('N/A')

    # 自動フォロー機構
    follower_list = api.followers(count=50)
    following_set = set([following.id for following in api.friends(count=50)])


    for follower in follower_list:
        des = follower.description
        # banned_words使ってたとき
        if re.search(banned_words, des):
            print('Cancelled to follow @{0}; using a banned word'.format(follower.id))

        elif follower.id in following_set:
            print('Cancelled to follow @{0}; already followed. '.format(follower.id))

        else:
            try:
                api.create_friendship(follower.id)
                print('Succeed in following @{0}'.format(follower.id))
            except:
                print('Unable to follow @{0}'.format(follower.id))
