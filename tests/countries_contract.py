#!/usr/bin/env python3
"""Full ISO 3166-1 alpha-2 country/flag support and normalization robustness."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import countries

# every assigned code produces a flag and a name
assert len(countries.ISO_COUNTRIES) >= 249
for code, name in countries.ISO_COUNTRIES.items():
    flag = countries.flag_for(code)
    assert flag != countries.UNKNOWN_FLAG and len(flag) >= 2, code
    assert countries.country_name(code) == name

# spot-check the regional-indicator math on a representative range
expect = {"FI": "🇫🇮", "DE": "🇩🇪", "US": "🇺🇸", "GB": "🇬🇧", "NL": "🇳🇱", "FR": "🇫🇷",
          "JP": "🇯🇵", "IR": "🇮🇷", "TR": "🇹🇷", "BR": "🇧🇷", "ZA": "🇿🇦", "AQ": "🇦🇶",
          "XK": "🇽🇰", "NZ": "🇳🇿", "SG": "🇸🇬", "AE": "🇦🇪"}
for code, flag in expect.items():
    assert countries.flag_for(code) == flag, (code, flag)

# case-insensitivity and whitespace
assert countries.flag_for(" fi ") == "🇫🇮"
assert countries.is_valid_code("us") and countries.is_valid_code("US") and not countries.is_valid_code("USA")
assert not countries.is_valid_code("") and not countries.is_valid_code(None) and not countries.is_valid_code("X1")

# normalization: codes, names, pairs in both orders, aliases, unknowns
cases = {
    "FI": ("Finland", "FI"), "fi": ("Finland", "FI"), " Finland ": ("Finland", "FI"),
    "FI | Finland": ("Finland", "FI"), "Finland | FI": ("Finland", "FI"),
    "DE | Germany": ("Germany", "DE"), "de": ("Germany", "DE"),
    "United States": ("United States", "US"), "USA": ("United States", "US"), "usa": ("United States", "US"),
    "South Korea": ("South Korea", "KR"), "UK": ("United Kingdom", "GB"),
    "Russia": ("Russia", "RU"), "Turkey": ("Turkey", "TR"), "Hong Kong": ("Hong Kong", "HK"),
    "Netherlands": ("Netherlands", "NL"), "Iran": ("Iran", "IR"),
}
for raw, want in cases.items():
    got = countries.normalize_country(raw)
    assert got == want, (raw, got, want)

# unknown / invalid values never crash and never invent codes
assert countries.normalize_country("Atlantis") == ("Atlantis", "")
assert countries.normalize_country("") == ("Unknown", "")
assert countries.normalize_country(None) == ("Unknown", "")
assert countries.normalize_country("123") == ("123", "")
assert countries.flag_for("Atlantis") == countries.UNKNOWN_FLAG
assert countries.flag_for("A1") == countries.UNKNOWN_FLAG

print(f"countries: {len(countries.ISO_COUNTRIES)} codes, flags=OK aliases=OK normalize=OK invalid=OK")
