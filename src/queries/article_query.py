from graphene import ObjectType, List, String
from src.services.article_service import ArticleService
from src.types import ArticleType

class ArticleQuery(ObjectType):
    articles = List(ArticleType, sports_type=String())

    def resolve_articles(self, info, sports_type=None):
        """
        Resolver for retrieving news articles, optionally filtered by sports_type.
        """
        return ArticleService.get_articles(sports_type)