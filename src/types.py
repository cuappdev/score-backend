from graphene import ObjectType, String


class TeamType(ObjectType):
    """
    A GraphQL type representing a team.

    Attributes:
        - `id`: The ID of the team (optional).
        - `color`: The color of the team.
        - `image`: The image of the team.
        - `name`: The name of the team.
    """

    id = String(required=False)
    color = String(required=True)
    image = String(required=True)
    name = String(required=True)

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class GameType(ObjectType):
    """
    A GraphQL type representing a game.

    Attributes:
        - `id`: The ID of the game (optional).
        - `city`: The city of the game.
        - `date`: The date of the game.
        - `gender`: The gender of the game.
        - `opponent_id`: The id of the opposing team.
        - `sport`: The sport of the game.
        - `state`: The state of the game.
        - `time`: The time of the game.
    """

    id = String(required=False)
    city = String(required=True)
    date = String(required=True)
    gender = String(required=True)
    opponent_id = String(required=True)
    sport = String(required=True)
    state = String(required=True)
    time = String(required=True)

    def __init__(self, id, city, date, gender, opponent_id, sport, state, time):
        self.id = id
        self.city = city
        self.date = date
        self.gender = gender
        self.opponent_id = opponent_id
        self.sport = sport
        self.state = state
        self.time = time
