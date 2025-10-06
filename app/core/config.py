from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "TaggedByBelle"
    debug: bool = True


settings = Settings()


