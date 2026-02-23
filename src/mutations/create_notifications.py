import graphene 
from graphene import Mutation
from src.services.notification_service import NotificationService

class CreateNotification(Mutation):
    class Arguments:
        tokens = graphene.List(graphene.String, required=True)
        title = graphene.String(required=True)
        body = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @staticmethod
    def mutate(root, info, tokens, title, body):
        try:
            response = NotificationService.send_notification(tokens, title, body)
            return CreateNotification(
                success=True,
                message=f"Notification sent to {response.success_count} device(s)."
            )
        except Exception as e:
            return CreateNotification(success=False, message=f"Error: {str(e)}")