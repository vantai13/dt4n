"""Unambiguous forward-facing names; preserve historical G4 APIs and hashes."""
from tools.g4_nugget_model import v_model, sf_model

KAPPA_NUGGET = 2.0
KAPPA_TIME_SIGNED = 5.0
KAPPA_ACCEPT = 1.0


def nugget_variance(cap_bps, dt, kappa_nugget=KAPPA_NUGGET):
    return v_model(cap_bps, dt, kappa=kappa_nugget)


def signal_fraction(sigma_link, cap_bps, dt, kappa_nugget=KAPPA_NUGGET):
    return sf_model(sigma_link, cap_bps, dt, kappa=kappa_nugget)
