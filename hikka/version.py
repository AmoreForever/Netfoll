"""Represents current userbot version"""
# ©️ Dan Gazizullin, 2021-2022
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html
# Morri and Penggrin modifided Hikka files for Netfoll
# 🌐 https://github.com/MXRRI/Netfoll

__version__ = (1, 6, 0)
netver = (0, 2, 0)
import os

import git

try:
    branch = git.Repo(
        path=os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    ).active_branch.name
except Exception:
    branch = "stable"
