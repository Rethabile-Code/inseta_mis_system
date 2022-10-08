import logging

_logger = logging.getLogger(__name__)


def dd2dms(dd1,dd2,ndec=6):
    """Convert a decimal degree coordinate pair to a six-tuple of degrees, minutes seconds.
    The returned values are not rounded.
    Arguments
    dd1, dd2 - coordinate pair, in decimal degrees
    Example
    >>> dd2dms(-74.25,32.1)
    (-74, 15, 6.9444444444444444e-05, 32, 6, 2.7777777777778172e-05)
    """
    # Author: Curtis Price, http://profile.usgs.gov/cprice
    # Disclaimer: Not approved by USGS. (Provisional, subject to revision.)    
    def ToDMS(dd):
        dd1 = abs(float(dd))
        cdeg = int(dd1)
        minsec = dd1 - cdeg
        cmin = int(minsec * 60)
        csec = (minsec % 60) / float(3600)    
        if dd < 0: cdeg = cdeg * -1
        return cdeg,cmin,csec 
    
    try:
        # return a six-tuple
        return ToDMS(dd1) + ToDMS(dd2)           
    except Exception as ex:
        _logger.exception(ex)