import re
import json
import tweepy

from . import constants
from . import db
from . import ai
from . import utils


twitter = tweepy.Client(constants.TWITTER_BEARER_TOKEN)


def twitter_search_posts(keyword, last_created_at):
    posts = []

    try:
        tweets = twitter.search_recent_tweets(
            query=f'{keyword} -is:retweet',
            tweet_fields=['id', 'text', 'created_at'],
            start_time=last_created_at,
            max_results=100
        )

        for tweet in tweets.data:
            posts.append({
                'post_id': tweet.id,
                'text': tweet.text,
                'created_at': tweet.created_at,
            })
    except Exception:
        return posts

    return posts


def twitter_insert_model_posts(model_repo_id, posts):
    for post in posts:
        try:
            values = []

            value = {
                'model_repo_id': model_repo_id,
                'post_id': post['post_id'],
                'clean_text': utils.clean_string(post['text']),
                'created_at': post['created_at'],
            }

            to_embedding = {
                'model_repo_id': value['model_repo_id'],
                'clean_text': value['clean_text']
            }

            embedding = str(ai.create_embedding(json.dumps(to_embedding)))
            values.append({**value, 'embedding': embedding})

            for chunk in utils.list_into_chunks([list(value.values()) for value in values]):
                with db.connection.cursor() as cursor:
                    cursor.executemany(f'''
                        INSERT INTO {constants.MODEL_TWITTER_POSTS_TABLE_NAME} (model_repo_id, post_id, clean_text, created_at, embedding)
                        VALUES (%s, %s, %s, %s, JSON_ARRAY_PACK(%s))
                    ''', chunk)
        except Exception as e:
            print('Error twitter_insert_model_posts: ', e)


def twitter_process_models_posts(existed_models):
    print('Processing Twitter posts')

    for model in existed_models:
        try:
            repo_id = model['repo_id']
            last_created_at = db.db_get_last_created_at(constants.MODEL_TWITTER_POSTS_TABLE_NAME, repo_id, True)
            keyword = model['name'] if re.search(r'\d', model['name']) else repo_id
            found_posts = twitter_search_posts(keyword, last_created_at)

            if len(found_posts):
                twitter_insert_model_posts(repo_id, found_posts)
        except Exception as e:
            print('Error twitter_process_models_posts: ', e)
