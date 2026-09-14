"""Metadata for historical T2 evidence; never invent an approved AoI/SLA axis."""
def pending_validity(kind, note):
    return {
        'schema':'dt4n.validity.v1', 'axis_role':kind,
        'pending_on':['aoi_axis'],
        'aoi_axis':{'label':'UNREGISTERED', 'note':note},
        'sla_axis':{'label':'UNREGISTERED',
                    'note':'No approved SLA claim is inferred from this historical diagnostic.'},
        'note':'Metadata completion only; no promotion or new adjudication. '+note,
    }
