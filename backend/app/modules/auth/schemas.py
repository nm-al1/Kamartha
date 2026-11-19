from pydantic import BaseModel, ConfigDict, Field, model_validator


class LoginInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=4, max_length=32, pattern=r"^[A-Za-z0-9._]+$")
    password: str = Field(min_length=1, max_length=128, repr=False)


class SetupInput(LoginInput):
    password: str = Field(min_length=8, max_length=128, repr=False)
    password_confirmation: str = Field(min_length=8, max_length=128, repr=False)
    setup_code: str = Field(min_length=1, max_length=128, repr=False)

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.password_confirmation:
            raise ValueError("Konfirmasi password tidak cocok.")
        return self


class ChangePasswordInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    old_password: str = Field(min_length=1, max_length=128, repr=False)
    password: str = Field(min_length=8, max_length=128, repr=False)
    password_confirmation: str = Field(min_length=8, max_length=128, repr=False)

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.password_confirmation:
            raise ValueError("Konfirmasi password tidak cocok.")
        return self
