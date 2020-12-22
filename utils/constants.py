from django.utils.translation import ugettext_lazy as _

(JAN, FEB, MAR, APR, MAY, JUN, JUL, AUG, SEP, OCT, NOV, DEC) = range(1, 13)
MONTH_CHOICES = (
    (JAN, _(u"January")),
    (FEB, _(u"February")),
    (MAR, _(u"March")),
    (APR, _(u"April")),
    (MAY, _(u"May")),
    (JUN, _(u"June")),
    (JUL, _(u"July")),
    (AUG, _(u"August")),
    (SEP, _(u"September")),
    (OCT, _(u"October")),
    (NOV, _(u"November")),
    (DEC, _(u"December")),
)
