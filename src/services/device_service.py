from src.repositories.device_repository import DeviceRepository
class DeviceService:
    @staticmethod
    def create_device(device_id, current_fcm_token, games, sports):
        """
        Create a new device.
        """
        return DeviceRepository.upsert(device_id, current_fcm_token, games, sports)