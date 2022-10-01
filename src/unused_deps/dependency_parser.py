from __future__ import annotations

import re
from typing import NamedTuple

_extra_feature_name_pattern = ""

# From PEP 508 https://peps.python.org/pep-0508/#complete-grammar:
#   specification = wsp* ( url_req | name_req ) wsp*
#   name_req      = name wsp* extras? wsp* versionspec? wsp* quoted_marker?
#   url_req       = name wsp* extras? wsp* urlspec wsp+ quoted_marker?
# we only care about the `name` part
_spec_re = re.compile(
    rf"""[ \t]*             
    (?P<name>
        [a-z0-9]                        # identifier
        (?:[a-z0-9_.\-]*[a-z0-9])*      # identifier_end
    )
    (?:
      [\t ]*;[\t ]*extra[\t ]*==[\t ]*
        "(?P<extra>
            # https://packaging.python.org/en/latest/specifications/core-metadata/#provides-extra-multiple-use
            (?:[a-z0-9]|[a-z0-9]([a-z0-9-](?!--))*[a-z0-9])+
         )"
    )?
    """,
    flags=re.IGNORECASE | re.VERBOSE,
)


class PackageInfo(NamedTuple):
    name: str
    extra: str | None


def get_name_from_spec(spec: str) -> PackageInfo | None:
    match = _spec_re.match(spec)
    if match is None:
        return None
    else:
        return PackageInfo(**match.groupdict())
