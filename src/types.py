from graphene import ObjectType, String, List, Int

class TeamType(ObjectType):
    """
    A GraphQL type representing a team.

    Attributes:
        - `id`: The ID of the team (optional).
        - `color`: The color of the team.
        - `image`: The image of the team (optional).
        - `name`: The name of the team.
    """

    id = String(required=False)
    color = String(required=True)
    image = String(required=False)
    name = String(required=True)

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class ScoringSummaryType(ObjectType):
    """
    Represents a single scoring summary entry in a game.

    Attributes:
        - `time`: The time at which the scoring event occurred.
        - `team`: The name of the team that scored.
        - `description`: A description of the scoring event.
    """
    time = String()
    team = String()
    description = String()

class BoxScoreEntryType(ObjectType):
    """
    Represents an individual entry in the box score of a game.

    Attributes:
        - `team`: The team involved in the scoring event.
        - `period`: The period or inning of the event.
        - `time`: The time of the scoring event.
        - `description`: A description of the play or scoring event.
        - `scorer`: The name of the scorer.
        - `assist`: The name of the assisting player.
        - `score_by`: Indicates which team scored.
        - `cor_score`: Cornell's score at the time of the event.
        - `opp_score`: Opponent's score at the time of the event.
    """
    
    team = String(required=False)
    period = String(required=False)
    time = String(required=False)
    description = String(required=False)
    scorer = String(required=False)
    assist = String(required=False)
    score_by = String(required=False)
    cor_score = Int(required=False)
    opp_score = Int(required=False)

class ScoreBreakdownType(ObjectType):
    """
    Represents the score breakdown for each period in a game.

    Attributes:
        - `scores`: A list of scores for each period of the game.
    """
    scores = List(String)

class GameType(ObjectType):
    """
    A GraphQL type representing a game.

    Attributes:
        - `id`: The ID of the game (optional).
        - `city`: The city of the game.
        - `date`: The date of the game.
        - `gender`: The gender of the game.
        - `location`: The location of the game. (optional)
        - `opponent_id`: The id of the opposing team.
        - `result`: The result of the game. (optional)
        - `sport`: The sport of the game.
        - `state`: The state of the game.
        - `box_score`: The box score of the game.
        - `score_breakdown`: The score breakdown of the game.
        - `time`: The time of the game. (optional)
        - `box_score`: The box score of the game.
        - `score_breakdown`: The score breakdown of the game.
    """

    id = String(required=False)
    city = String(required=True)
    date = String(required=True)
    gender = String(required=True)
    location = String(required=False)
    opponent_id = String(required=True)
    result = String(required=False)
    sport = String(required=True)
    state = String(required=True)
    time = String(required=False)
    box_score = List(BoxScoreEntryType, required=False)
    score_breakdown = List(List(String), required=False)

    def __init__(
        self, id, city, date, gender, location, opponent_id, result, sport, state, time, box_score=None, score_breakdown=None
    ):
        self.id = id
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
