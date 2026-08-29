"""One function per provider, and the dict that names them.

The collector contract, for anything rendering this:

    Collector = Callable[[Sources], ProviderUsage]
    COLLECTORS: dict[str, Collector]

Add a provider by adding one function and one dict entry. A collector must return a
`ProviderUsage` for every input -- including "the payload is not there" -- and must
never raise: a provider that is absent degrades to `not_configured`, which is a fact
about the installation, while `unavailable` is a fact about the provider.

The providers here are deliberately unalike, and the difference is the record this file
exists to keep. Codex is the one subscription whose headroom schema was measured on this
machine, so its figures are tagged `measured`. Claude's is vendor-documented and has
never been parsed here, so its figures are tagged `cited`. Cursor and Grok were measured
to expose no individual remaining-allowance counter at all, and each carries the finding
that would have to be overturned for that to change. OpenRouter's spend is read from the
trajectory rather than from a live counter, because a live counter was measured reading
zero while the spend was real. Each collector's own docstring carries its evidence; none
of it is repeated here, because a second copy is a second thing to drift."""

from .usage_model import (
    COLLECTORS,
    Collector,
    ProviderUsage,
    Quota,
    Sources,
    Spend,
)


__all__ = [
    "COLLECTORS",
    "Collector",
    "ProviderUsage",
    "Quota",
    "Sources",
    "Spend",
]
