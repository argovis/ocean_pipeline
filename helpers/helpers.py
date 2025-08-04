import numpy, datetime, scipy.interpolate, scipy.integrate, math, operator, juliandate, bisect, warnings, xarray

def mljul(year, month, day, time):
    # compute something appropriate to interpret as matlab's julian day

    julian = juliandate.from_gregorian(year, month, day)
    if time is None or numpy.isnan(julian):
        return julian
    else:
        return julian + time/24

def datenum_to_datetime(dn):
    # MATLAB datenum: days since Jan 0, 0000
    return datetime.datetime.fromordinal(int(dn)) + \
           datetime.timedelta(days=dn % 1) - \
           datetime.timedelta(days=366)

def datetime_to_datenum(dt):
    matlab_epoch = datetime.datetime(1, 1, 1)  # Python datetime has no year 0
    delta = dt - matlab_epoch
    return delta.days + delta.seconds / 86400 + 366 + 1

def remap_longitude(longitude):
    # map longitudes onto [20,380)

    while longitude < 20:
        longitude += 360
    while longitude >= 380:
        longitude -= 360
    return longitude

def find_bracket(lst, low_roi, high_roi):
    # lst: ordered list of floats
    # low_roi: lower bound of region of interest
    # high_roi: upper bound "
    # returns the indexes of the last element below and first element above the ROI, without running off ends of list

    if low_roi <= lst[0]:
        low_index = 0
    else:
        low = 0
        high = len(lst) - 1
        low_index = -1

        while low <= high:
            mid = (low + high) // 2

            if lst[mid] < low_roi:
                low_index = mid
                low = mid + 1
            else:
                high = mid - 1

    if high_roi >= lst[-1]:
        high_index = len(lst) - 1
    else:
        low = 0
        high = len(lst) - 1
        high_index = -1

        while low <= high:
            mid = (low + high) // 2

            if lst[mid] > high_roi:
                high_index = mid
                high = mid - 1
            else:
                low = mid + 1

    return low_index, high_index

def pad_bracket(lst, low_roi, high_roi, buffer, places):
    # returns the indexes of the last element below and first element above an ROI padded with <buffer>, and containing at least <places> elements in the padding.

    tight_bracket = find_bracket(lst, low_roi, high_roi)
    buffer_bracket = find_bracket(lst, low_roi - buffer, high_roi + buffer)

    low = buffer_bracket[0]
    if tight_bracket[0] - buffer_bracket[0] < places-1: # -1 since find_bracket gives the first bound in the wing, so there's already one point in the wing even for tight_bracket
        low = max(0, tight_bracket[0] - places+1)

    high = buffer_bracket[1]
    if buffer_bracket[1] - tight_bracket[1] < places-1:
        high = min(len(lst)-1, tight_bracket[1] + places-1)

    return low, high

def tidy_profile(pressure, var, flag):
    # pchip needs pressures to be monotonically increasing; WOD needs some tidying in this regard.
    # also need the dependent variable to always be defined
    # flags (little endian):
    # 1: degenerate adjacent levels
    # 2: levels in reverse order
    # 4: variable of interest was NaN, masked
    # 8: levels non-monotonic, had to sort
    # 32: pressure was NaN, masked

    ## dependent variable must be defined
    mask = [0]*len(var)
    for i in range(len(var)):
        if var[i] is None or math.isnan(var[i]):
            mask[i] = 1
            flag = flag | 4
    p = [pressure[i] for i in range(len(mask)) if mask[i]==0]
    v = [var[i] for i in range(len(mask)) if mask[i]==0]

    ## pressure must be defined
    mask = [0]*len(p)
    for i in range(len(p)):
        if p[i] is None or math.isnan(p[i]):
            mask[i] = 1
            flag = flag | 32
    p = [p[i] for i in range(len(mask)) if mask[i]==0]
    v = [v[i] for i in range(len(mask)) if mask[i]==0]

    ## drop degenerate levels and flag
    mask = [0]*len(p)
    for i in range(len(p)-1):
        if p[i] == p[i+1]:
            mask[i] = 1
            mask[i+1] = 1
            flag = flag | 1
    p = [p[i] for i in range(len(mask)) if mask[i]==0]
    v = [v[i] for i in range(len(mask)) if mask[i]==0]

    if all(p[i] < p[i + 1] for i in range(len(p) - 1)):
        # pressure is monotonically increasing, return
        return p, v, flag

    if all(p[i] > p[i + 1] for i in range(len(p) - 1)):
        # pressure is monotonically decreasing, reverse and return
        flag = flag | 2
        return p[::-1], v[::-1], flag

    # pressure is non-monotonic, sort and try again
    x = sorted(zip(p,v))
    p = [element[0] for element in x]
    v = [element[1] for element in x]
    flag = flag | 8
    return tidy_profile(p,v,flag)


def interpolate_to_levels(row, var, levels, pressure_buffer=100.0, pressure_index_buffer=5):
    # interpolate <var> to <levels> using PCHIP interpolation
    # keep <pressure_buffer> dbar on either side of the ROI and <pressure_index_buffer> points in the pressure buffer margins, at least.
    # flag 16 (little endian): ROI didn't contain enough info to interpolate

    pressure, variable, flag = tidy_profile(row['pressure'], row[var], row['flag'])

    # some truly pathological profiles will have no levels left at this point
    if len(pressure) == 0:
        interp = numpy.full(len(levels), numpy.nan)
        flag = flag | 16
        return interp, flag

    # find indexes of ROI
    p_bracket = pad_bracket(pressure, levels[0], levels[-1], pressure_buffer, pressure_index_buffer)

    # ROI must contain at least two points for Pchip
    if len(pressure[p_bracket[0]:p_bracket[1]+1]) < 2:
        interp = numpy.full(len(levels), numpy.nan)
        flag = flag | 16
        return interp, flag
    else:
        # interpolate; don't extrapolate to levels outside of measurement range
        interp = scipy.interpolate.PchipInterpolator(pressure[p_bracket[0]:p_bracket[1]+1], variable[p_bracket[0]:p_bracket[1]+1], extrapolate=False)(levels)

        # if there wasn't a measured level within a certain radius of each level of interest, mask the interpolation at that level.
        #interp = mask_far_interps(pressure[p_bracket[0]:p_bracket[1]+1], levels, interp)

        return interp, flag

def integrate_roi(pressure, variable, low_roi, high_roi):
    # trapezoidal integration of <variable> over <pressure> from <low_roi> to <high_roi>.
    # will error out if <low_roi> and/or <high_roi> are not found in <pressure>.
    # will return nan if any nans in pressure or variable

    low_i = int(numpy.where(pressure == low_roi)[0][0])
    high_i = int(numpy.where(pressure == high_roi)[0][0])
    return scipy.integrate.trapezoid(variable[low_i:high_i+1], x=pressure[low_i:high_i+1])

def filterQCandPressure(t,s,p, t_qc,s_qc,p_qc, pressure_qc, temperature_qc, salinity_qc, pressure):
    # keep only levels where p, t and psal have qc flags found in <pressure_qc>, <temperature_qc>, and <salinity_qc> respectively, and pressure is below <pressure>.
    data = list(zip(t,s,p,t_qc,s_qc,p_qc))
    goodTPS = list(filter(lambda level: level[3] in temperature_qc and level[4] in salinity_qc and level[5] in pressure_qc and level[2]<pressure, data))
    t_filter = [x[0] for x in goodTPS]
    p_filter = [x[2] for x in goodTPS]
    s_filter = [x[1] for x in goodTPS]
    tqc_filter = [x[3] for x in goodTPS]
    pqc_filter = [x[5] for x in goodTPS]
    sqc_filter = [x[4] for x in goodTPS]

    return t_filter, s_filter, p_filter, tqc_filter, sqc_filter, pqc_filter

def mask_far_interps(measured_pressures, interp_levels, interp_values):
    # mask interpolated values that are too far from the nearest measured pressure

    for i, level in enumerate(interp_levels):
        ## determine how far is too far:
        radius = 0
        if level < 100:
            radius = 10
        elif level < 150:
            radius = 20
        elif level < 250:
            radius = 40
        elif level < 350:
            radius = 60
        elif level < 450:
            radius = 80
        elif level < 550:
            radius = 100
        elif level < 650:
            radius = 120
        elif level < 750:
            radius = 140
        elif level < 850:
            radius = 160
        else:
            radius = 180

        i_below = 0
        i_above = len(measured_pressures)-1
        for j in range(len(measured_pressures)):
            if measured_pressures[j] <= level:
                i_below = j
            else:
                i_above = j
                break
        if abs(measured_pressures[i_below] - level) > radius or abs(measured_pressures[i_above] - level) > radius:
            interp_values[i] = numpy.nan

    return interp_values

def integration_region(region, pressure, variable):
    # perform intrgation of <variable> over <pressure> for a list of <regions> specified as tuples of (low_roi, high_roi)
    low_roi, high_roi = region
    integrals = integrate_roi(pressure, variable, low_roi, high_roi)

    return [integrals]

def integration_comb(region, spacing=0.2):
    # generates a level spectrum with <spacing> levels populating the <region>

    pressure = []
    low_roi, high_roi = region
    pressure.extend(numpy.arange(low_roi, high_roi+spacing, spacing))
    
    return numpy.round(pressure, 6)

def choose_profile(group):
    # prefer the highest resolution profile as calculated over the depth range covered by all profiles in the group
    # allow a slightly lower res profile if it goes deeper

    df = group.copy()
    shallowest = df['pressure'].apply(lambda lst: lst[-1]).min()
    df['resolution'] = df['pressure'].apply(lambda lst: len(lst[:bisect.bisect_right(lst, shallowest)])/shallowest)

    preferred = 0
    for i in range(len(group)):
        if (
            df.iloc[i]['resolution'] >= 1.15*df.iloc[preferred]['resolution'] # insurmountably higher resolution, depth is irrelevant
            or df.iloc[i]['resolution'] > df.iloc[preferred]['resolution'] and df.iloc[i]['pressure'][-1] >= df.iloc[preferred]['pressure'][-1] # slightly higher resolution and deeper
        ):
            preferred = i

    return group.iloc[preferred]

def merge_qc(qc_lists):
    return [max(column) for column in zip(*qc_lists)]

def mld_estimator(row):
    # estimate the mixed layer depth for this profile
    # row['potential_density'] == gsw potential density from which to estimate MLD threshold

    reference_depth = 10
    reference_density = interpolate_to_levels(row, 'potential_density', [reference_depth])[0][0]
    if numpy.isnan(reference_density):
        return [None]
    threshold_density = reference_density + 0.03

    # go fishing for the depth that corresponds to the threshold
    return [pchip_search(threshold_density, 0, 1000, 1, row, 'potential_density')]


def pchip_search(target, init_min, init_max, init_step, row, variable):
    threshold = 0.0001
    guess = -99999
    fguess = -99999
    range_min = max(init_min, min(row['pressure']))
    range_max = min(init_max, max(row['pressure']))
    comb = numpy.arange(range_min, range_max + init_step, init_step)
    iterations = 0

    while abs(fguess - target) > threshold and iterations < 100 and range_max > range_min:
        fcomb, flag = interpolate_to_levels(row, variable, comb)
        lower = None
        upper = None
        # find the first bracket around the target value
        for i in range(len(fcomb)-1):
            if fcomb[i] <= target and fcomb[i+1] > target:
                lower = i
                upper = i+1
                break
        if lower is None:
            return None # nothing brackets the target value, give up
        guess = comb[lower]
        fguess = fcomb[lower]
        range_min = comb[lower]
        range_max = comb[upper]
        if range_max == range_min:
            break
        stepsize = (range_max - range_min) / 10
        comb = numpy.arange(range_min, range_max + stepsize, stepsize)
        iterations += 1

    if abs(fguess - target) < threshold:
        return guess
    else:
        return None

def safe_open_dataset(fn):
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always", RuntimeWarning)
        try:
            xar = xarray.open_dataset(fn)
        except Exception as e:
            print(f"❌ Could not open {fn}: {e}")
            return None

        for warning in w:
            if "invalid value encountered in cast" in str(warning.message):
                # happens once in a while, seems like an automatic time conversion choke
                date = xar['JULD'].to_dict()['data'][0]
                juldqc = int(xar['JULD_QC'].to_dict()['data'][0])
                refdate = xar['REFERENCE_DATE_TIME'].to_dict()['data']
                print(f"⚠️ Time cast warning in: {fn}; JULD: {str(date)}, JULD_QC: {juldqc}, REFERENCE_DATE_TIME: {refdate}")

        return xar
