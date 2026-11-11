from graphene import Mutation, String

from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required


class RefreshAccessToken(Mutation):
    new_access_token = String()

    @jwt_required(refresh=True)
    def mutate(self, info):
        identity = get_jwt_identity()
        return RefreshAccessToken(
            new_access_token=create_access_token(identity=identity),
        )
