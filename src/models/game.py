from bson.objectid import ObjectId


class Game:
    """
    A model representing a game.

    Attributes:
        - `city`            The city of the game.
        - `date`            The date of the game.
        - `gender`          The gender of the game.
        - `location`        The location of the game. (optional)
        - `opponent_id`     The id of the opposing team.
        - `result`          The result of the game. (optional)
        - `sport`           The sport of the game.
        - `state`           The state of the game.
        - `time`            The time of the game. (optional)
        - `box_score`       The scoring summary of the game (optional)
        - `score_breakdown` The scoring breakdown of the game (optional)
        - 'ticket_link'    The ticket link for the game (optional)
        - 'recap_link'     The recap/details link for the game (optional)
        - 'recap_article_title' Title from the recap/story page when scraped (optional)
        - 'recap_published_at'  Published date/time string from the recap page (optional)
        - 'recap_article_image' Primary image URL from the recap page (optional)
    """

    def __init__(
        self,
        city,
        date,
        gender,
        opponent_id,
        sport,
        state,
        id=None,
        location=None,
        result=None,
        time=None,
        box_score=None,
        score_breakdown=None,
        team=None,
        utc_date=None,
        ticket_link=None,
        recap_link=None,
        recap_article_title=None,
        recap_published_at=None,
        recap_article_image=None,
    ):
        self.id = id if id else str(ObjectId())
        self.city = city
        self.date = date
        self.gender = gender
        self.location = location
        self.opponent_id = opponent_id
        self.result = result
        self.sport = sport
        self.state = state
        self.time = time
        self.box_score = box_score
        self.score_breakdown = score_breakdown
        self.team = team
        self.utc_date = utc_date
        self.ticket_link = ticket_link
        self.recap_link = recap_link
        self.recap_article_title = recap_article_title
        self.recap_published_at = recap_published_at
        self.recap_article_image = recap_article_image

    def to_dict(self):
        """
        Converts the Game object to a dictionary format for MongoDB storage.
        """
        return {
            "_id": self.id,
            "city": self.city,
            "date": self.date,
            "gender": self.gender,
            "location": self.location,
            "opponent_id": self.opponent_id,
            "result": self.result,
            "sport": self.sport,
            "state": self.state,
            "time": self.time,
            "box_score": self.box_score,
            "score_breakdown": self.score_breakdown,
            "team": self.team,
            "utc_date": self.utc_date,
            "ticket_link": self.ticket_link,
            "recap_link": self.recap_link,
            "recap_article_title": self.recap_article_title,
            "recap_published_at": self.recap_published_at,
            "recap_article_image": self.recap_article_image,
        }

    @staticmethod
    def from_dict(data) -> None:
        """
        Converts a MongoDB document to a Game object.
        """
        return Game(
            id=data.get("_id"),
            city=data.get("city"),
            date=data.get("date"),
            gender=data.get("gender"),
            location=data.get("location"),
            opponent_id=data.get("opponent_id"),
            result=data.get("result"),
            sport=data.get("sport"),
            state=data.get("state"),
            time=data.get("time"),
            box_score=data.get("box_score"),
            score_breakdown=data.get("score_breakdown"),
            team=data.get("team"),
            utc_date=data.get("utc_date"),
            ticket_link=data.get("ticket_link"),
            recap_link=data.get("recap_link"),
            recap_article_title=data.get("recap_article_title"),
            recap_published_at=data.get("recap_published_at"),
            recap_article_image=data.get("recap_article_image"),
        )
