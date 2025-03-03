# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html
# Netfoll Team modifided Hikka files for Netfoll
# 🌐 https://github.com/MXRRI/Netfoll

import asyncio
import io
import logging
import os
import re

from telethon.errors.rpcerrorlist import YouBlockedUserError
from telethon.tl.functions.contacts import UnblockRequest

from .. import utils
from .._internal import fw_protect
from .types import InlineUnit

logger = logging.getLogger(__name__)

with open(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "assets", "bot_pfp.png")
    ),
    "rb",
) as f:
    photo = io.BytesIO(f.read())
    photo.name = "avatar.png"


class TokenObtainment(InlineUnit):
    async def _create_bot(self):
        # This is called outside of conversation, so we can start the new one
        # We create new bot
        logger.info("User doesn't have bot, attempting creating new one")
        async with self._client.conversation("@BotFather", exclusive=False) as conv:
            await fw_protect()
            m = await conv.send_message("/newbot")
            r = await conv.get_response()

            logger.debug(">> %s", m.raw_text)
            logger.debug("<< %s", r.raw_text)

            if "20" in r.raw_text:
                return False

            await fw_protect()
            await m.delete()
            await r.delete()

            if self._db.get("hikka.inline", "custom_bot", False):
                username = self._db.get("hikka.inline", "custom_bot").strip("@")
                username = f"@{username}"
                try:
                    await self._client.get_entity(username)
                except ValueError:
                    pass
                else:
                    # Generate and set random username for bot
                    uid = utils.rand(6)
                    username = f"@netfoll_{uid}_bot"
            else:
                # Generate and set random username for bot
                uid = utils.rand(6)
                username = f"@netfoll_{uid}_bot"

            for msg in [
                f"👾 Netfoll Userbot of {self._name}"[:64],
                username,
                "/setuserpic",
                username,
            ]:
                await fw_protect()
                m = await conv.send_message(msg)
                r = await conv.get_response()

                logger.debug(">> %s", m.raw_text)
                logger.debug("<< %s", r.raw_text)

                await fw_protect()
                await m.delete()
                await r.delete()

            try:
                await fw_protect()
                m = await conv.send_file(photo)
                r = await conv.get_response()

                logger.debug(">> <Photo>")
                logger.debug("<< %s", r.raw_text)
            except Exception:
                # In case user was not able to send photo to
                # BotFather, it is not a critical issue, so
                # just ignore it
                await fw_protect()
                m = await conv.send_message("/cancel")
                r = await conv.get_response()

                logger.debug(">> %s", m.raw_text)
                logger.debug("<< %s", r.raw_text)

            await fw_protect()

            await m.delete()
            await r.delete()

        # Re-attempt search. If it won't find newly created (or not created?) bot
        # it will return `False`, that's why `init_complete` will be `False`
        return await self._assert_token(False)

    async def _assert_token(
        self,
        create_new_if_needed: bool = True,
        revoke_token: bool = False,
    ) -> bool:
        # If the token is set in db
        if self._token:
            # Just return `True`
            return True

        logger.info("Netfoll can't find token in database, taking it from BotFather")

        if not self._db.get(__name__, "no_mute", False):
            await utils.dnd(
                self._client,
                await self._client.get_entity("@BotFather"),
                True,
            )
            self._db.set(__name__, "no_mute", True)

        # Start conversation with BotFather to attempt search
        async with self._client.conversation("@BotFather", exclusive=False) as conv:
            # Wrap it in try-except in case user banned BotFather
            try:
                # Try sending command
                await fw_protect()
                m = await conv.send_message("/token")
            except YouBlockedUserError:
                # If user banned BotFather, unban him
                await self._client(UnblockRequest(id="@BotFather"))
                # And resend message
                await fw_protect()
                m = await conv.send_message("/token")

            r = await conv.get_response()

            logger.debug(">> %s", m.raw_text)
            logger.debug("<< %s", r.raw_text)

            await fw_protect()

            await m.delete()
            await r.delete()

            # User do not have any bots yet, so just create new one
            if not hasattr(r, "reply_markup") or not hasattr(r.reply_markup, "rows"):
                # Cancel current conversation (search)
                # bc we don't need it anymore
                await conv.cancel_all()

                return await self._create_bot() if create_new_if_needed else False

            for row in r.reply_markup.rows:
                for button in row.buttons:
                    if self._db.get(
                        "hikka.inline", "custom_bot", False
                    ) and self._db.get(
                        "hikka.inline", "custom_bot", False
                    ) != button.text.strip(
                        "@"
                    ):
                        continue

                    if not self._db.get(
                        "hikka.inline",
                        "custom_bot",
                        False,
                    ) and not re.search(r"@netfoll_[0-9a-zA-Z]{6}_bot", button.text):
                        continue

                    m = await conv.send_message(button.text)
                    r = await conv.get_response()

                    logger.debug(">> %s", m.raw_text)
                    logger.debug("<< %s", r.raw_text)

                    if revoke_token:
                        await fw_protect()
                        await m.delete()
                        await r.delete()

                        await fw_protect()

                        m = await conv.send_message("/revoke")
                        r = await conv.get_response()

                        logger.debug(">> %s", m.raw_text)
                        logger.debug("<< %s", r.raw_text)

                        await fw_protect()

                        await m.delete()
                        await r.delete()

                        await fw_protect()

                        m = await conv.send_message(button.text)
                        r = await conv.get_response()

                        logger.debug(">> %s", m.raw_text)
                        logger.debug("<< %s", r.raw_text)

                    token = r.raw_text.splitlines()[1]

                    # Save token to database, now this bot is ready-to-use
                    self._db.set("hikka.inline", "bot_token", token)
                    self._token = token

                    await fw_protect()

                    await m.delete()
                    await r.delete()

                    # Enable inline mode or change its
                    # placeholder in case it is not set

                    for msg in [
                        "/setinline",
                        button.text,
                        "👾 Inline-Commands...",
                        "/setinlinefeedback",
                        button.text,
                        "Enabled",
                        "/setuserpic",
                        button.text,
                    ]:
                        await fw_protect()
                        m = await conv.send_message(msg)
                        r = await conv.get_response()

                        await fw_protect()

                        logger.debug(">> %s", m.raw_text)
                        logger.debug("<< %s", r.raw_text)

                        await m.delete()
                        await r.delete()

                    try:
                        await fw_protect()
                        m = await conv.send_file(photo)
                        r = await conv.get_response()

                        logger.debug(">> <Photo>")
                        logger.debug("<< %s", r.raw_text)
                    except Exception:
                        # In case user was not able to send photo to
                        # BotFather, it is not a critical issue, so
                        # just ignore it
                        await fw_protect()
                        m = await conv.send_message("/cancel")
                        r = await conv.get_response()

                        logger.debug(">> %s", m.raw_text)
                        logger.debug("<< %s", r.raw_text)

                    await fw_protect()
                    await m.delete()
                    await r.delete()

                    # Return `True` to say, that everything is okay
                    return True

        # And we are not returned after creation
        return await self._create_bot() if create_new_if_needed else False

    async def _reassert_token(self):
        is_token_asserted = await self._assert_token(revoke_token=True)
        if not is_token_asserted:
            self.init_complete = False
        else:
            await self.register_manager(ignore_token_checks=True)

    async def _dp_revoke_token(self, already_initialised: bool = True):
        if already_initialised:
            await self._stop()
            logger.error("Got polling conflict. Attempting token revocation...")

        self._db.set("hikka.inline", "bot_token", None)
        self._token = None
        if already_initialised:
            asyncio.ensure_future(self._reassert_token())
        else:
            return await self._reassert_token()
