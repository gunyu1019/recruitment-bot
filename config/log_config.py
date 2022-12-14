"""GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007

Copyright (c) 2021 gunyu1019

PUBG BOT is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

PUBG BOT is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with PUBG BOT.  If not, see <https://www.gnu.org/licenses/>.
"""

import logging

from utils.directory import directory

logging_format = logging.Formatter(
    "[%(asctime)s | %(name)s | %(levelname)s]: %(message)s", "%Y-%m-%d %p %I:%M:%S"
)


def get_logger(name: str = None):
    _log = logging.getLogger(name)
    _log.setLevel(logging.INFO)
    return _log


log = get_logger()
command = logging.StreamHandler()
command.setFormatter(logging_format)
log.addHandler(command)
