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

import pytz

COUNTRY_TIMEZONES = {
    "AD": pytz.timezone("Europe/Andorra"),
    "AL": pytz.timezone("Europe/Tirane"),
    "AM": pytz.timezone("Asia/Yerevan"),
    "AR": pytz.timezone("America/Argentina/Buenos_Aires"),
    "AT": pytz.timezone("Europe/Vienna"),
    "AU": pytz.timezone("Australia/Sydney"),
    "AX": pytz.timezone("Europe/Mariehamn"),
    "BA": pytz.timezone("Europe/Sarajevo"),
    "BB": pytz.timezone("America/Barbados"),
    "BE": pytz.timezone("Europe/Brussels"),
    "BG": pytz.timezone("Europe/Sofia"),
    "BJ": pytz.timezone("Africa/Porto-Novo"),
    "BO": pytz.timezone("America/La_Paz"),
    "BR": pytz.timezone("America/Sao_Paulo"),
    "BS": pytz.timezone("America/Nassau"),
    "BW": pytz.timezone("Africa/Gaborone"),
    "BY": pytz.timezone("Europe/Minsk"),
    "BZ": pytz.timezone("America/Belize"),
    "CA": pytz.timezone("America/Toronto"),
    "CH": pytz.timezone("Europe/Zurich"),
    "CL": pytz.timezone("America/Santiago"),
    "CN": pytz.timezone("Asia/Shanghai"),
    "CO": pytz.timezone("America/Bogota"),
    "CR": pytz.timezone("America/Costa_Rica"),
    "CU": pytz.timezone("America/Havana"),
    "CY": pytz.timezone("Asia/Nicosia"),
    "CZ": pytz.timezone("Europe/Prague"),
    "DE": pytz.timezone("Europe/Berlin"),
    "DK": pytz.timezone("Europe/Copenhagen"),
    "DO": pytz.timezone("America/Santo_Domingo"),
    "EC": pytz.timezone("America/Guayaquil"),
    "EE": pytz.timezone("Europe/Tallinn"),
    "EG": pytz.timezone("Africa/Cairo"),
    "ES": pytz.timezone("Europe/Madrid"),
    "FI": pytz.timezone("Europe/Helsinki"),
    "FO": pytz.timezone("Atlantic/Faroe"),
    "FR": pytz.timezone("Europe/Paris"),
    "GA": pytz.timezone("Africa/Libreville"),
    "GB": pytz.timezone("Europe/London"),
    "GD": pytz.timezone("America/Grenada"),
    "GE": pytz.timezone("Asia/Tbilisi"),
    "GG": pytz.timezone("Europe/Guernsey"),
    "GI": pytz.timezone("Europe/Gibraltar"),
    "GL": pytz.timezone("America/Nuuk"),
    "GM": pytz.timezone("Africa/Banjul"),
    "GR": pytz.timezone("Europe/Athens"),
    "GT": pytz.timezone("America/Guatemala"),
    "GY": pytz.timezone("America/Guyana"),
    "HK": pytz.timezone("Asia/Hong_Kong"),
    "HN": pytz.timezone("America/Tegucigalpa"),
    "HR": pytz.timezone("Europe/Zagreb"),
    "HT": pytz.timezone("America/Port-au-Prince"),
    "HU": pytz.timezone("Europe/Budapest"),
    "ID": pytz.timezone("Asia/Jakarta"),
    "IE": pytz.timezone("Europe/Dublin"),
    "IM": pytz.timezone("Europe/Isle_of_Man"),
    "IS": pytz.timezone("Atlantic/Reykjavik"),
    "IT": pytz.timezone("Europe/Rome"),
    "JE": pytz.timezone("Europe/Jersey"),
    "JM": pytz.timezone("America/Jamaica"),
    "JP": pytz.timezone("Asia/Tokyo"),
    "KR": pytz.timezone("Asia/Seoul"),
    "KZ": pytz.timezone("Asia/Almaty"),
    "LI": pytz.timezone("Europe/Vaduz"),
    "LS": pytz.timezone("Africa/Maseru"),
    "LT": pytz.timezone("Europe/Vilnius"),
    "LU": pytz.timezone("Europe/Luxembourg"),
    "LV": pytz.timezone("Europe/Riga"),
    "MA": pytz.timezone("Africa/Casablanca"),
    "MC": pytz.timezone("Europe/Monaco"),
    "MD": pytz.timezone("Europe/Chisinau"),
    "ME": pytz.timezone("Europe/Podgorica"),
    "MG": pytz.timezone("Indian/Antananarivo"),
    "MK": pytz.timezone("Europe/Skopje"),
    "MN": pytz.timezone("Asia/Ulaanbaatar"),
    "MS": pytz.timezone("America/Montserrat"),
    "MT": pytz.timezone("Europe/Malta"),
    "MX": pytz.timezone("America/Mexico_City"),
    "MZ": pytz.timezone("Africa/Maputo"),
    "NA": pytz.timezone("Africa/Windhoek"),
    "NE": pytz.timezone("Africa/Niamey"),
    "NG": pytz.timezone("Africa/Lagos"),
    "NI": pytz.timezone("America/Managua"),
    "NL": pytz.timezone("Europe/Amsterdam"),
    "NO": pytz.timezone("Europe/Oslo"),
    "NZ": pytz.timezone("Pacific/Auckland"),
    "PA": pytz.timezone("America/Panama"),
    "PE": pytz.timezone("America/Lima"),
    "PG": pytz.timezone("Pacific/Port_Moresby"),
    "PH": pytz.timezone("Asia/Manila"),
    "PL": pytz.timezone("Europe/Warsaw"),
    "PR": pytz.timezone("America/Puerto_Rico"),
    "PT": pytz.timezone("Europe/Lisbon"),
    "PY": pytz.timezone("America/Asuncion"),
    "RO": pytz.timezone("Europe/Bucharest"),
    "RS": pytz.timezone("Europe/Belgrade"),
    "RU": pytz.timezone("Europe/Moscow"),
    "SE": pytz.timezone("Europe/Stockholm"),
    "SG": pytz.timezone("Asia/Singapore"),
    "SI": pytz.timezone("Europe/Ljubljana"),
    "SJ": pytz.timezone("Arctic/Longyearbyen"),
    "SK": pytz.timezone("Europe/Bratislava"),
    "SM": pytz.timezone("Europe/San_Marino"),
    "SR": pytz.timezone("America/Paramaribo"),
    "SV": pytz.timezone("America/El_Salvador"),
    "TN": pytz.timezone("Africa/Tunis"),
    "TR": pytz.timezone("Europe/Istanbul"),
    "UA": pytz.timezone("Europe/Kyiv"),
    "US": pytz.timezone("America/New_York"),
    "UY": pytz.timezone("America/Montevideo"),
    "VA": pytz.timezone("Europe/Vatican"),
    "VE": pytz.timezone("America/Caracas"),
    "VN": pytz.timezone("Asia/Ho_Chi_Minh"),
    "ZA": pytz.timezone("Africa/Johannesburg"),
    "ZW": pytz.timezone("Africa/Harare"),
}

VALID_COUNTRY_CODES = {
    "AD",
    "AL",
    "AM",
    "AR",
    "AT",
    "AU",
    "AX",
    "BA",
    "BB",
    "BE",
    "BG",
    "BJ",
    "BO",
    "BR",
    "BS",
    "BW",
    "BY",
    "BZ",
    "CA",
    "CH",
    "CL",
    "CN",
    "CO",
    "CR",
    "CU",
    "CY",
    "CZ",
    "DE",
    "DK",
    "DO",
    "EC",
    "EE",
    "EG",
    "ES",
    "FI",
    "FO",
    "FR",
    "GA",
    "GB",
    "GD",
    "GE",
    "GG",
    "GI",
    "GL",
    "GM",
    "GR",
    "GT",
    "GY",
    "HK",
    "HN",
    "HR",
    "HT",
    "HU",
    "ID",
    "IE",
    "IM",
    "IS",
    "IT",
    "JE",
    "JM",
    "JP",
    "KR",
    "KZ",
    "LI",
    "LS",
    "LT",
    "LU",
    "LV",
    "MA",
    "MC",
    "MD",
    "ME",
    "MG",
    "MK",
    "MN",
    "MS",
    "MT",
    "MX",
    "MZ",
    "NA",
    "NE",
    "NG",
    "NI",
    "NL",
    "NO",
    "NZ",
    "PA",
    "PE",
    "PG",
    "PH",
    "PL",
    "PR",
    "PT",
    "PY",
    "RO",
    "RS",
    "RU",
    "SE",
    "SG",
    "SI",
    "SJ",
    "SK",
    "SM",
    "SR",
    "SV",
    "TN",
    "TR",
    "UA",
    "US",
    "UY",
    "VA",
    "VE",
    "VN",
    "ZA",
    "ZW",
}
