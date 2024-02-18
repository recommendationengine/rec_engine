import src.db as db
from src.constants import MODELS_LIMIT
from src.github import github_process_models_repos
from src.leaderboard import leaderboard_process_models
from src.reddit import reddit_process_models_posts
from src.twitter import twitter_process_models_posts

# db.drop_table('models')
# db.drop_table('model_readmes')
# db.drop_table('model_twitter_posts')
# db.drop_table('model_reddit_posts')
# db.drop_table('model_github_repos')

db.create_tables()

leaderboard_process_models()

existed_models = db.get_models('repo_id, name', f'ORDER BY score DESC LIMIT {MODELS_LIMIT}')

twitter_process_models_posts(existed_models)
reddit_process_models_posts(existed_models)
github_process_models_repos(existed_models)
