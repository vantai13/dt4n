"""20R2.9-A4: omitted experimental choices fail before any IO or computation."""
class _MustChoose:
    __slots__ = ()
    def __repr__(self):
        return "<MUST_CHOOSE explicitly>"
    def __bool__(self):
        raise TypeError("An experimental choice was omitted")

MUST_CHOOSE = _MustChoose()

def require_choice(value, name):
    if isinstance(value, _MustChoose) or (value is None and name in
            {"calibration_path", "axis", "sigma"}):
        raise ValueError(f"{name} must be chosen explicitly; no experimental default. "
                         "Pass the intended artifact/axis, including legacy only for a "
                         "named historical replay or control.")
    return value
