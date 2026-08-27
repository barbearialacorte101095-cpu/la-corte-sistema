import os


class Settings:
    """Configurações da aplicação, lidas de variáveis de ambiente."""

    DATABASE_URL: str = os.environ.get("DATABASE_URL", "")
    ALLOWED_ORIGINS: list[str] = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
    ENV: str = os.environ.get("VERCEL_ENV", "development")

    def validate(self) -> None:
        if not self.DATABASE_URL:
            raise RuntimeError(
                "DATABASE_URL não configurada. Defina essa variável de ambiente "
                "com a connection string do pooler do Supabase (porta 6543)."
            )


settings = Settings()
