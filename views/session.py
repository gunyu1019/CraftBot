import discord
import asyncio
from flask import Blueprint
from flask import session
from flask import redirect
from flask import render_template
from flask import request
from flask import make_response
from flask import jsonify
from flask import url_for
from typing import List, Tuple, Callable, NamedTuple

from config.config import get_config
from modules.microsoft import Microsoft
from modules.errors import HttpException


bp = Blueprint(
    name="session",
    import_name="session",
    url_prefix="/session"
)
bot: discord.Client

parser = get_config()
client = Microsoft(
    client_id=parser.get("microsoft-oauth2", "client_id"),
    client_secret=parser.get("microsoft-oauth2", "client_secret")
)
scope = parser.get("microsoft-oauth2", "scope").split()


@bp.route("/logout", methods=['GET'])
def logout():
    for key in list(session.keys()):
        del session[key]

    return redirect(
        url_for("index.index")
    )


@bp.route("/login", methods=['GET'])
def login():
    state = request.args.get("state", None)
    if state is None:
        return make_response("wrong approach", 403)
    return redirect(
        client.authorize(
            redirect_uri="http://" + request.host + "/session/callback",
            scope=scope,
            state=state
        )
    )


@bp.route("/callback", methods=['GET'])
async def callback():
    code = request.args.get("code", None)
    state = request.args.get("state", None)
    if code is None or state is None:
        return make_response("wrong approach", 403)

    try:
        access_token = await client. generate_access_token(
            code=code,
            redirect_uri="http://" + request.host + "/session/callback"
        )
    except HttpException as error:
        return make_response(jsonify({
            "title": error.data.get("error"),
            "message": error.data.get("error_description"),
            "process": "Access Token"
        }), error.response_code)

    if access_token.token == "":
        return redirect(
            url_for("session.login")
        )

    event = "login_success"
    listeners: List[Tuple[asyncio.Future, Callable[..., bool]]] = getattr(bot, "_listeners", {}).get(event)

    # Dispatch (coroutine)
    if listeners is not None:
        removed = []
        for i, (future, condition) in enumerate(listeners):
            if future.cancelled():
                removed.append(i)
                continue

            try:
                result = condition(state, access_token)
            except Exception as exc:
                future.set_exception(exc)
                removed.append(i)
            else:
                if result:
                    future.set_result((state, access_token))
                    removed.append(i)

        if len(removed) == len(listeners):
            getattr(bot, "_listeners", {}).pop(event)
        else:
            for idx in reversed(removed):
                del listeners[idx]

    try:
        coroutine = getattr(bot, "on_" + event)
    except AttributeError:
        pass
    else:
        await coroutine(state, access_token)

    return render_template('success.html')
