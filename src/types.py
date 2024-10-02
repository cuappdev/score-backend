from graphene import ObjectType, String


class GameType(ObjectType):
    city = String()
    date = String()
    gender = String()
    opponent_id = String()
    sport = String()
    state = String()
    time = String()

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
