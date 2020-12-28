from django.utils.translation import ugettext_lazy as _

# Metrics
KILOGRAM = 'kg'
HECTOGRAM = 'hg'  # similar to ONS
GRAM = 'g'
MILLIGRAM = 'mg'
LITER = 'liter'
PACK = 'pack'
POUCH = 'pouch'
BOTTLE = 'bottle'
PIECE = 'piece'
BUNCH = 'bunch'
SACK = 'sack'
BOX = 'box'
UNIT = 'unit'
CUP = 'cup'
CANS = 'cans'
NOMINAL = 'nominal'
JOINTLY = 'jointly'
METRIC_CHOICES = (
    (NOMINAL, _("Nominal")),
    (KILOGRAM, _("Kilogram")),
    (HECTOGRAM, _("Ons")),
    (GRAM, _("Gram")),
    (MILLIGRAM, _("Miligram")),
    (LITER, _("Liter")),
    (PACK, _("Bungkus")),
    (POUCH, _("Kantung")),
    (BOTTLE, _("Botol")),
    (CUP, _("Cup")),
    (PIECE, _("Buah")),
    (BUNCH, _("Ikat")),
    (SACK, _("Karung")),
    (BOX, _("Kotak")),
    (CANS, _("Kaleng")),
    (JOINTLY, _("Renteng")),
    (UNIT, _("Unit")),
)


WAITING = 'waiting'
ACCEPT = 'accept'
REJECT = 'reject'
GENERAL_STATUS = (
    (WAITING, _("Menunggu")),
    (ACCEPT, _("Terima")),
    (REJECT, _("Tolak")),
)
