from graphene import Mutation, String, Field, List
from src.types import DeviceType
from src.services.device_service import DeviceService

class CreateDevice(Mutation):
    class Arguments:
        device_id = String(required=True)
        current_fcm_token = String(required=True)
        games = List(String)
        sports = List(String)

    device = Field(lambda: DeviceType)
    def mutate(self, info, device_id, current_fcm_token, games, sports):
        new_device = DeviceService.create_device(device_id, current_fcm_token, games, sports)
        return CreateDevice(device=new_device)