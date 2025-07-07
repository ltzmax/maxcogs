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

import typing
from datetime import datetime

import discord
import pytz
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_number


def dashboard_page(*args, **kwargs):
    def decorator(func: typing.Callable):
        func.__dashboard_decorator_params__ = (args, kwargs)
        return func

    return decorator


class DashboardIntegration:
    bot: Red

    @commands.Cog.listener()
    async def on_dashboard_cog_add(self, dashboard_cog: commands.Cog) -> None:
        """Register this cog with the dashboard."""
        dashboard_cog.rpc.third_parties_handler.add_third_party(self)

    @dashboard_page(name="stats", description="View AutoPublisher statistics", is_owner=True)
    async def dashboard_stats(self, user: discord.User, **kwargs) -> typing.Dict[str, typing.Any]:
        """Dashboard page to display AutoPublisher stats."""
        owner_tz = await self._get_owner_timezone()
        data = await self.config.all()
        last_count_time = data.get("last_count_time", "Never")
        last_published = "Never"
        if last_count_time != "Never":
            try:
                last_count_dt = datetime.fromisoformat(last_count_time)
                last_count_dt = last_count_dt.replace(tzinfo=pytz.UTC).astimezone(owner_tz)
                last_published = last_count_dt.strftime("%Y-%m-%d %H:%M:%S %Z")
            except ValueError:
                last_published = "Invalid timestamp"

        table_data = [
            ["Weekly", humanize_number(data.get("published_weekly_count", 0))],
            ["Monthly", humanize_number(data.get("published_monthly_count", 0))],
            ["Yearly", humanize_number(data.get("published_yearly_count", 0))],
            ["Total Published", humanize_number(data.get("published_count", 0))],
        ]
        table_html = (
            "<table border='1' style='border-collapse: collapse; width: 50%; margin: auto;'>"
        )
        table_html += "<tr><th>Period</th><th>Count</th></tr>"
        for period, count in table_data:
            table_html += f"<tr><td>{period}</td><td>{count}</td></tr>"
        table_html += "</table>"

        source = f"""
        <h3>AutoPublisher Statistics</h3>
        {table_html}
        <p><strong>Timezone:</strong> {owner_tz.zone}</p>
        <p><strong>Last Published:</strong> {last_published}</p>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; }}
            table {{ margin: 20px auto; }}
            th, td {{ padding: 10px; border: 1px solid #ddd; }}
            th {{ background-color: #61BA92; }}
        </style>
        """

        return {
            "status": 0,
            "web_content": {
                "source": source,
            },
        }
