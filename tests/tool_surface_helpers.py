"""The reversible set, shared by the classifier unit and the admission unit.

Family "external" and default shell (no proven sandbox) are the irreversible set; class
3 (subagent) is delegated and is in neither; class 1 is the file family, and that is
what this constant holds. It is derived from the live ``REGISTERED_TOOLS`` table rather
than written out, so a tool added to the inventory is covered without anyone remembering
to update a list here.

It sits in both units because the same set carries two different claims: the classifier
must keep it at class 1, and admission must still execute a recoverable file mutation
against it. That is the utility being paid for, not a missed attack.

Deliberately not named ``test_*.py``, so pytest does not collect it."""

from consilient.capabilities import (
    REGISTERED_TOOLS,
)

REVERSIBLE_DEFAULT = tuple(
    (kind, name)
    for (kind, name), family in sorted(REGISTERED_TOOLS.items())
    if family == "file"
)
