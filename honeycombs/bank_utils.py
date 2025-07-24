"""
MIT License

Copyright (c) 2022-present ltzmax

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import discord
from redbot.core import bank
from redbot.core.errors import BankError

# Tried to make stuff shorter in honeycombs.py but somehow made it longer, so this file got kinda pointless
# But i already had writen stuff so there's no point removing right away... i'll do someday when im less lazy.


async def safe_withdraw(user: discord.Member, amount: int, currency_name: str) -> tuple[bool, str]:
    """
    Safely withdraw credits from a user's bank account.

    Args:
        user: The Discord member to withdraw credits from.
        amount: The amount to withdraw.
        currency_name: The name of the currency for error messaging.

    Returns:
        Tuple[bool, str]: (success, message)
        - success: True if withdrawal succeeded, False otherwise.
        - message: A message describing the outcome (success or error).
    """
    if amount < 0:
        return False, f"Cannot withdraw a negative amount of {currency_name}."

    try:
        current_balance = await bank.get_balance(user)
        if current_balance < amount:
            return (
                False,
                f"{user.mention} has insufficient {currency_name} ({current_balance} < {amount}).",
            )

        await bank.withdraw_credits(user, amount)
        return True, f"Withdrew {amount} {currency_name} from {user.mention}."

    except BankError as e:
        return False, f"Failed to withdraw {amount} {currency_name} from {user.mention}: {str(e)}"


async def safe_deposit(user: discord.Member, amount: int, currency_name: str) -> tuple[bool, str]:
    """
    Safely deposit credits to a user's bank account.

    Args:
        user: The Discord member to deposit credits to.
        amount: The amount to deposit.
        currency_name: The name of the currency for error messaging.

    Returns:
        Tuple[bool, str]: (success, message)
        - success: True if deposit succeeded, False otherwise.
        - message: A message describing the outcome (success or error).
    """
    if amount < 0:
        return False, f"Cannot deposit a negative amount of {currency_name}."

    try:
        await bank.deposit_credits(user, amount)
        return True, f"Deposited {amount} {currency_name} to {user.mention}."

    except BankError as e:
        return False, f"Failed to deposit {amount} {currency_name} to {user.mention}: {str(e)}"
