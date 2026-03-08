from src.config import CustomBaseSettings


class GoogleConfig(CustomBaseSettings):
    BUCKET_NAME: str


settings = GoogleConfig()
