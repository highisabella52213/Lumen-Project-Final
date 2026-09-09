"""Full ISO 3166-1 alpha-2 country support: names, codes, and flag emoji.

The flag for a valid alpha-2 code is generated generically from its regional
indicator symbols, so every ISO code works — no hand-picked shortlist.
"""
from __future__ import annotations

import re

# ISO 3166-1 alpha-2 → English short name (complete current assignment set).
ISO_COUNTRIES = {
    "AD": "Andorra", "AE": "United Arab Emirates", "AF": "Afghanistan",
    "AG": "Antigua and Barbuda", "AI": "Anguilla", "AL": "Albania",
    "AM": "Armenia", "AO": "Angola", "AQ": "Antarctica", "AR": "Argentina",
    "AS": "American Samoa", "AT": "Austria", "AU": "Australia", "AW": "Aruba",
    "AX": "Åland Islands", "AZ": "Azerbaijan", "BA": "Bosnia and Herzegovina",
    "BB": "Barbados", "BD": "Bangladesh", "BE": "Belgium", "BF": "Burkina Faso",
    "BG": "Bulgaria", "BH": "Bahrain", "BI": "Burundi", "BJ": "Benin",
    "BL": "Saint Barthélemy", "BM": "Bermuda", "BN": "Brunei", "BO": "Bolivia",
    "BQ": "Caribbean Netherlands", "BR": "Brazil", "BS": "Bahamas",
    "BT": "Bhutan", "BV": "Bouvet Island", "BW": "Botswana", "BY": "Belarus",
    "BZ": "Belize", "CA": "Canada", "CC": "Cocos (Keeling) Islands",
    "CD": "DR Congo", "CF": "Central African Republic", "CG": "Congo",
    "CH": "Switzerland", "CI": "Côte d'Ivoire", "CK": "Cook Islands",
    "CL": "Chile", "CM": "Cameroon", "CN": "China", "CO": "Colombia",
    "CR": "Costa Rica", "CU": "Cuba", "CV": "Cape Verde", "CW": "Curaçao",
    "CX": "Christmas Island", "CY": "Cyprus", "CZ": "Czechia", "DE": "Germany",
    "DJ": "Djibouti", "DK": "Denmark", "DM": "Dominica", "DO": "Dominican Republic",
    "DZ": "Algeria", "EC": "Ecuador", "EE": "Estonia", "EG": "Egypt",
    "EH": "Western Sahara", "ER": "Eritrea", "ES": "Spain", "ET": "Ethiopia",
    "FI": "Finland", "FJ": "Fiji", "FK": "Falkland Islands", "FM": "Micronesia",
    "FO": "Faroe Islands", "FR": "France", "GA": "Gabon", "GB": "United Kingdom",
    "GD": "Grenada", "GE": "Georgia", "GF": "French Guiana", "GG": "Guernsey",
    "GH": "Ghana", "GI": "Gibraltar", "GL": "Greenland", "GM": "Gambia",
    "GN": "Guinea", "GP": "Guadeloupe", "GQ": "Equatorial Guinea",
    "GR": "Greece", "GS": "South Georgia", "GT": "Guatemala", "GU": "Guam",
    "GW": "Guinea-Bissau", "GY": "Guyana", "HK": "Hong Kong",
    "HM": "Heard Island and McDonald Islands", "HN": "Honduras", "HR": "Croatia",
    "HT": "Haiti", "HU": "Hungary", "ID": "Indonesia", "IE": "Ireland",
    "IL": "Israel", "IM": "Isle of Man", "IN": "India", "IO": "British Indian Ocean Territory",
    "IQ": "Iraq", "IR": "Iran", "IS": "Iceland", "IT": "Italy", "JE": "Jersey",
    "JM": "Jamaica", "JO": "Jordan", "JP": "Japan", "KE": "Kenya",
    "KG": "Kyrgyzstan", "KH": "Cambodia", "KI": "Kiribati", "KM": "Comoros",
    "KN": "Saint Kitts and Nevis", "KP": "North Korea", "KR": "South Korea",
    "KW": "Kuwait", "KY": "Cayman Islands", "KZ": "Kazakhstan", "LA": "Laos",
    "LB": "Lebanon", "LC": "Saint Lucia", "LI": "Liechtenstein",
    "LK": "Sri Lanka", "LR": "Liberia", "LS": "Lesotho", "LT": "Lithuania",
    "LU": "Luxembourg", "LV": "Latvia", "LY": "Libya", "MA": "Morocco",
    "MC": "Monaco", "MD": "Moldova", "ME": "Montenegro", "MF": "Saint Martin",
    "MG": "Madagascar", "MH": "Marshall Islands", "MK": "North Macedonia",
    "ML": "Mali", "MM": "Myanmar", "MN": "Mongolia", "MO": "Macao",
    "MP": "Northern Mariana Islands", "MQ": "Martinique", "MR": "Mauritania",
    "MS": "Montserrat", "MT": "Malta", "MU": "Mauritius", "MV": "Maldives",
    "MW": "Malawi", "MX": "Mexico", "MY": "Malaysia", "MZ": "Mozambique",
    "NA": "Namibia", "NC": "New Caledonia", "NE": "Niger", "NF": "Norfolk Island",
    "NG": "Nigeria", "NI": "Nicaragua", "NL": "Netherlands", "NO": "Norway",
    "NP": "Nepal", "NR": "Nauru", "NU": "Niue", "NZ": "New Zealand",
    "OM": "Oman", "PA": "Panama", "PE": "Peru", "PF": "French Polynesia",
    "PG": "Papua New Guinea", "PH": "Philippines", "PK": "Pakistan",
    "PL": "Poland", "PM": "Saint Pierre and Miquelon", "PN": "Pitcairn",
    "PR": "Puerto Rico", "PS": "Palestine", "PT": "Portugal", "PW": "Palau",
    "PY": "Paraguay", "QA": "Qatar", "RE": "Réunion", "RO": "Romania",
    "RS": "Serbia", "RU": "Russia", "RW": "Rwanda", "SA": "Saudi Arabia",
    "SB": "Solomon Islands", "SC": "Seychelles", "SD": "Sudan", "SE": "Sweden",
    "SG": "Singapore", "SH": "Saint Helena", "SI": "Slovenia",
    "SJ": "Svalbard and Jan Mayen", "SK": "Slovakia", "SL": "Sierra Leone",
    "SM": "San Marino", "SN": "Senegal", "SO": "Somalia", "SR": "Suriname",
    "SS": "South Sudan", "ST": "São Tomé and Príncipe", "SV": "El Salvador",
    "SX": "Sint Maarten", "SY": "Syria", "SZ": "Eswatini",
    "TC": "Turks and Caicos Islands", "TD": "Chad", "TF": "French Southern Territories",
    "TG": "Togo", "TH": "Thailand", "TJ": "Tajikistan", "TK": "Tokelau",
    "TL": "Timor-Leste", "TM": "Turkmenistan", "TN": "Tunisia", "TO": "Tonga",
    "TR": "Turkey", "TT": "Trinidad and Tobago", "TV": "Tuvalu",
    "TW": "Taiwan", "TZ": "Tanzania", "UA": "Ukraine", "UG": "Uganda",
    "UM": "U.S. Minor Outlying Islands", "US": "United States", "UY": "Uruguay",
    "UZ": "Uzbekistan", "VA": "Vatican City", "VC": "Saint Vincent and the Grenadines",
    "VE": "Venezuela", "VG": "British Virgin Islands", "VI": "U.S. Virgin Islands",
    "VN": "Vietnam", "VU": "Vanuatu", "WF": "Wallis and Futuna", "WS": "Samoa",
    "YE": "Yemen", "YT": "Mayotte", "ZA": "South Africa", "ZM": "Zambia",
    "ZW": "Zimbabwe", "XK": "Kosovo",
}

# Common alternative spellings / short aliases → alpha-2 code.
_ALIASES = {
    "usa": "US", "america": "US", "united states of america": "US",
    "u.s.": "US", "u.s.a.": "US", "us": "US",
    "uk": "GB", "great britain": "GB", "britain": "GB", "england": "GB",
    "u.k.": "GB",
    "uae": "AE", "emirates": "AE",
    "south korea": "KR", "korea": "KR", "republic of korea": "KR",
    "north korea": "KP",
    "russia": "RU", "russian federation": "RU",
    "iran": "IR", "iran (islamic republic of)": "IR",
    "turkey": "TR", "turkiye": "TR", "türkiye": "TR",
    "czech republic": "CZ",
    "hong kong": "HK", "hongkong": "HK", "hong kong sar": "HK",
    "macau": "MO",
    "taiwan": "TW", "taiwan, province of china": "TW", "chinese taipei": "TW",
    "vietnam": "VN", "viet nam": "VN",
    "laos": "LA", "lao pdr": "LA", "syria": "SY", "syrian arab republic": "SY",
    "palestine": "PS", "state of palestine": "PS",
    "democratic republic of the congo": "CD", "drc": "CD", "congo kinshasa": "CD",
    "republic of the congo": "CG", "congo brazzaville": "CG",
    "ivory coast": "CI", "cote d'ivoire": "CI",
    "cabo verde": "CV",
    "holland": "NL", "the netherlands": "NL",
    "vatican": "VA", "holy see": "VA",
    "swaziland": "SZ",
    "burma": "MM",
    "east timor": "TL",
    "south georgia and the south sandwich islands": "GS",
    "brunei darussalam": "BN",
    "federated states of micronesia": "FM",
    "sao tome and principe": "ST",
    "saint vincent": "VC", "saint kitts": "KN",
    "virgin islands (u.s.)": "VI", "virgin islands (british)": "VG",
    "curacao": "CW",
    "reunion": "RE",
    "aland islands": "AX", "aland": "AX",
}

# casefolded official name → code (built once from ISO_COUNTRIES).
_NAME_TO_CODE = {}
for _code, _name in ISO_COUNTRIES.items():
    _NAME_TO_CODE.setdefault(_name.casefold(), _code)
for _alias, _code in _ALIASES.items():
    if _code in ISO_COUNTRIES:
        _NAME_TO_CODE.setdefault(_alias, _code)

_CODE_RE = re.compile(r"^[A-Za-z]{2}$")
UNKNOWN_FLAG = "🌐"

# Exceptionally reserved / transitional codes that must map to the assigned one.
_CODE_ALIASES = {"UK": "GB", "EL": "GR", "BU": "MM", "TP": "TL", "YU": "RS", "ZR": "CD"}


def is_valid_code(value) -> bool:
    """True for any assigned ISO 3166-1 alpha-2 code, any letter case."""
    return isinstance(value, str) and value.strip().upper() in ISO_COUNTRIES


def country_name(code) -> str:
    """Official short name for a valid code, else the uppercased code itself."""
    return ISO_COUNTRIES.get(str(code or "").strip().upper(), str(code or "").strip().upper())


def flag_for(code) -> str:
    """Regional-indicator flag for any valid ISO alpha-2 code; 🌐 otherwise.

    The mapping is purely mechanical (A→🇦 … Z→🇿), so every assigned code
    produces its flag without a hand-maintained emoji table.
    """
    code = str(code or "").strip().upper()
    if not _CODE_RE.fullmatch(code):
        return UNKNOWN_FLAG
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in code)


def normalize_country(raw) -> tuple:
    """Normalize repository/UI country metadata to (display_name, alpha-2 code).

    Accepts: "FI", "fi", " Finland ", "FI | Finland", "Finland | FI",
    "United States", "USA", "South Korea", … Unknown or unparseable values
    return (cleaned_raw, "") and never raise.
    """
    text = str(raw or "").strip()
    if not text:
        return "Unknown", ""

    # Code + name pair in either order ("FI | Finland" or "Finland | FI").
    if "|" in text:
        left, right = (part.strip() for part in text.split("|", 1))
        for maybe_code, maybe_name in ((left, right), (right, left)):
            if _CODE_RE.fullmatch(maybe_code):
                code = maybe_code.upper()
                code = _CODE_ALIASES.get(code, code)
                name = maybe_name or country_name(code)
                return name[:60], code

    if _CODE_RE.fullmatch(text):
        code = text.upper()
        code = _CODE_ALIASES.get(code, code)
        return country_name(code), code

    code = _NAME_TO_CODE.get(text.casefold())
    if code:
        return country_name(code), code

    # A name we do not know: keep it readable, but do not invent a code.
    return text[:60], ""
