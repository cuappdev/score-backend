from graphene import Mutation, String, Field
from src.types import GameType
from src.services import GameService


class CreateGame(Mutation):
    class Arguments:
        city = String(required=True)
        date = String(required=True)
        gender = String(required=True)
        location = String(required=False)
        opponent_id = String(required=True)
        result = String(required=False)
        sport = String(required=True)
        state = String(required=True)
        time = String(required=True)
        box_score = String(required=False)
        score_breakdown = String(required=False)
        utc_date = String(required=False)
        ticket_link = String(required=False)
        recap_link = String(required=False)
        recap_article_title = String(required=False)
        recap_published_at = String(required=False)
        recap_article_image = String(required=False)

    game = Field(lambda: GameType)

    def mutate(
        self,
        info,
        city,
        date,
        gender,
        opponent_id,
        sport,
        state,
        location=None,
        result=None,
        time=None,
        box_score=None,
        score_breakdown=None,
        utc_date=None,
        ticket_link=None,
        recap_link=None,
        recap_article_title=None,
        recap_published_at=None,
        recap_article_image=None,
    ):
        game_data = {
            "city": city,
            "date": date,
            "gender": gender,
            "location": location,
            "opponent_id": opponent_id,
            "result": result,
            "sport": sport,
            "state": state,
            "time": time,
            "box_score": box_score,
            "score_breakdown": score_breakdown,
            "utc_date": utc_date,
            "ticket_link": ticket_link,
            "recap_link": recap_link,
            "recap_article_title": recap_article_title,
            "recap_published_at": recap_published_at,
            "recap_article_image": recap_article_image,
        }
        new_game = GameService.create_game(game_data)
        return CreateGame(game=new_game)
