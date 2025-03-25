from graphene import Mutation, String, Field
from src.types import ArticleType
from src.services.article_service import ArticleService

class CreateArticle(Mutation):
    class Arguments:
        title = String(required=True)
        sports_type = String(required=True)
        published_at = String(required=True)
        url = String(required=True)
        slug = String(required=True)
        image = String(required=False)

    article = Field(lambda: ArticleType)

    def mutate(self, info, title, sports_type, published_at, url, slug, image=None):
        from datetime import datetime
        article_data = {
            "title": title,
            "sports_type": sports_type,
            "published_at": datetime.fromisoformat(published_at),
            "url": url,
            "slug": slug,
            "image": image
        }
        new_article = ArticleService.create_article(article_data)
        return CreateArticle(article=new_article)