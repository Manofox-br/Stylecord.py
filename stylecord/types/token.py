import httpx

from ..errors import errors

REST_API = "https://discord.com/api/v10"

class Token(str):
    MIN_LENGTH = 50
    MAX_LENGTH = 100

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value, info):
        if not isinstance(value, str):
            raise errors.InvalidTokenError("A token must be a string.")

        if not (cls.MIN_LENGTH <= len(value) <= cls.MAX_LENGTH):
            raise errors.InvalidTokenError("Token with invalid size.")

        if not cls._check_token(value):
            raise errors.InvalidTokenError("Token rejected by the Discord API.")

        return cls(value)
    
    @staticmethod
    def _check_token(token:str) -> bool:
        try:
            with httpx.Client(timeout=5) as client:
                r = client.get(
                    f"{REST_API}/users/@me",
                    headers={"Authorization": f"Bot {token}"}
                )
                return r.status_code == 200
        except httpx.RequestError:
            return False