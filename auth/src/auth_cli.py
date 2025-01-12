import typer
import asyncio


from rich import print
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.entity import User, Role
from db.postgres import async_session

MIN_PASSWORD_LEN = 10

cli = typer.Typer()


def get_and_validate_user_data() -> tuple[str, str]:
    login = typer.prompt("login")
    if len(login) == 0:
        print("[red]Login cannot be empty[/red]")
        raise typer.Exit(1)

    password = typer.prompt("password", hide_input=True)
    password_check = typer.prompt("password (one more time)", hide_input=True)

    if password != password_check:
        print("[red]Passwords don't match[/red]")
        raise typer.Exit(1)

    if len(password) < MIN_PASSWORD_LEN:
        confirm = typer.confirm(
            "Password is too short. Do you want to continue?"
        )
        if not confirm:
            raise typer.Abort()

    return login, password


async def user_exists(login: str, session: AsyncSession) -> bool:
    statement = select(User).filter(User.login == login)
    result = await session.execute(statement)
    return result.scalar_one_or_none() is not None


async def superuser_role_exists(session: AsyncSession) -> Role | None:
    statement = select(Role).filter(Role.name == "superuser")
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def create_superuser_role_if_not_exists(session: AsyncSession) -> Role:
    role = await superuser_role_exists(session)
    if role is not None:
        return role

    role = Role(name="superuser", description="Role with maximum access")
    session.add(role)
    await session.commit()
    print("Superuser role created in DB")
    return role


async def add_superuser(login: str, passwd: str):
    async with async_session() as session:
        exists = await user_exists(login, session)
        if exists:
            print(
                f"[red]Login [bold]{login}[/bold] already exists. "
                "Please, select different login [/red]"
            )
            raise typer.Exit(1)
        su = User(login=login, password=passwd)
        role = await create_superuser_role_if_not_exists(session)
        su.roles.append(role)

        session.add(su)
        await session.commit()
    return


@cli.command("createsuperuser", short_help="Create superuser")
def createsuperuser():
    login, password = get_and_validate_user_data()

    asyncio.run(add_superuser(login, password))
    print(f"[green]User [bold]{login}[/bold] created successfully[/green]")


@cli.command(short_help="Does nothing")
def second_command(): ...


if __name__ == "__main__":
    cli()
