ID_TYPES = [
    ('dni', 'DNI'),
    ('ce', 'Carnet de extranjería'),
    ('passport', 'Pasaporte'),
    ('other', 'Otro'),
]

IMAGING_STATE_CHOICES = [
    ('preview', 'Vista previa'),
    ('ready', 'Lista'),
    ('processing', 'Procesando'),
    ('analyzed', 'Analizada'),
    ('error', 'Error'),
]

MALIGNANCY_TYPES = [
    ('0', 'Altamente Improbable'),
    ('1', 'Moderadamente Improbable'),
    ('2', 'Indeterminado'),
    ('3', 'Moderadamente Sospechoso'),
    ('4', 'Altamente Sospechoso'),
]