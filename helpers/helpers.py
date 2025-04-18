import numpy, datetime, scipy.interpolate, scipy.integrate, math, operator, juliandate, bisect

def mljul(year, month, day, time):
    # compute something appropriate to interpret as matlab's julian day

    julian = juliandate.from_gregorian(year, month, day)
    if time is None or numpy.isnan(julian):
        return julian
    else:
        return julian + time/24

def remap_longitude(longitude):
    # map longitudes onto [20,380)

    while longitude < 20:
        longitude += 360
    while longitude >= 380:
        longitude -= 360
    return longitude

def has_common_non_nan_value(list1, list2):
    for i in range(len(list1)):
        if not (list1[i] is None or list2[i] is None) and not (math.isnan(list1[i]) or math.isnan(list2[i])):
            return True
    return False

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
    # flags (little endian):
    # 1: degenerate adjacent levels
    # 2: levels in reverse order
    # 4: levels non-monotonic, had to sort

    ## drop degenerate levels and flag
    mask = [0]*len(pressure)
    for i in range(len(pressure)-1):
        if pressure[i] == pressure[i+1]:
            mask[i] = 1
            mask[i+1] = 1
            flag = flag | 1
    p = [pressure[i] for i in range(len(mask)) if mask[i]==0]
    v = [var[i] for i in range(len(mask)) if mask[i]==0]

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
    flag = flag | 4
    return tidy_profile(p,v,flag)


def interpolate_to_levels(row, var, levels, pressure_buffer=100.0, pressure_index_buffer=5):
    # interpolate <var> to <levels> using PCHIP interpolation
    # keep <pressure_buffer> dbar on either side of the ROI and <pressure_index_buffer> points in the pressure buffer margins, at least.
    # flag 8 (little endian): ROI didn't contain enough info to interpolate

    pressure, variable, flag = tidy_profile(row['pressure'], row[var], row['flag'])

    # some truly pathological profiles will have no levels left at this point
    if len(pressure) == 0:
        interp = numpy.full(len(levels), numpy.nan)
        flag = flag | 8
        return interp, flag

    # find indexes of ROI
    p_bracket = pad_bracket(pressure, levels[0], levels[-1], pressure_buffer, pressure_index_buffer)

    # ROI must contain at least two points for Pchip
    if len(pressure[p_bracket[0]:p_bracket[1]+1]) < 2:
        interp = numpy.full(len(levels), numpy.nan)
        flag = flag | 8
        return interp, flag
    else:
        # interpolate; don't extrapolate to levels outside of measurement range
        interp = scipy.interpolate.PchipInterpolator(pressure[p_bracket[0]:p_bracket[1]+1], variable[p_bracket[0]:p_bracket[1]+1], extrapolate=False)(levels)

        # if there wasn't a measured level within a certain radius of each level of interest, mask the interpolation at that level.
        interp = mask_far_interps(pressure[p_bracket[0]:p_bracket[1]+1], levels, interp)

        return interp, flag

def interpolate_and_integrate(pressures, temperatures, low_roi, high_roi):
    # perform a trapezoidal integration with pressures=x and temperatures=y, from pressure==low_roi to high_roi

    levels = numpy.arange(low_roi, high_roi+0.2, 0.2) # fine level spectrum across the ROI
    t_interp = scipy.interpolate.pchip_interpolate(pressures, temperatures, levels)

    integration_region = find_bracket(levels, low_roi, high_roi)
    p_integration = levels[integration_region[0] : integration_region[1]+1]
    t_integration = t_interp[integration_region[0] : integration_region[1]+1]

    return scipy.integrate.trapezoid(t_integration, x=p_integration)

def integrate_roi(pressure, variable, low_roi, high_roi):
    # trapezoidal integration of <variable> over <pressure> from <low_roi> to <high_roi>.
    # will error out if <low_roi> and/or <high_roi> are not found in <pressure>.

    low_i = int(numpy.where(pressure == low_roi)[0][0])
    high_i = int(numpy.where(pressure == high_roi)[0][0])
    return scipy.integrate.trapezoid(variable[low_i:high_i+1], x=pressure[low_i:high_i+1])

# def filterQC(t,s,p, t_qc,s_qc,p_qc, acceptable):
#     # given <t>emperature, <s>alinity and <p>ressure lists for a profile,
#     # the corresponding <>_qc flags,
#     # and an <acceptable> list of qc flags,
#     # return t,s and p lists with levels dropped if t or p aren't acceptable qc,
#     # if t and p are good but s isn't, mask s with NaN.

#     data = list(zip(t,s,p,t_qc,s_qc,p_qc))
#     goodTP = list(filter(lambda level: level[3] in acceptable and level[5] in acceptable, data))
#     t_filter = [x[0] for x in goodTP]
#     p_filter = [x[2] for x in goodTP]
#     s_filter = [x[1] if x[4] in acceptable else numpy.NAN for x in goodTP]

#     return t_filter, s_filter, p_filter

def filterQCandPressure(t,s,p, t_qc,s_qc,p_qc, acceptable, pressure):
    # keep only levels where t, psal and p all have <acceptable> qc flags, and pressure is below <pressure>.
    data = list(zip(t,s,p,t_qc,s_qc,p_qc))
    goodTPS = list(filter(lambda level: level[3] in acceptable and level[4] in acceptable and level[5] in acceptable and level[2]<pressure, data))
    t_filter = [x[0] for x in goodTPS]
    p_filter = [x[2] for x in goodTPS]
    s_filter = [x[1] for x in goodTPS]
    tqc_filter = [x[3] for x in goodTPS]
    pqc_filter = [x[5] for x in goodTPS]
    sqc_filter = [x[4] for x in goodTPS]

    return t_filter, s_filter, p_filter, tqc_filter, sqc_filter, pqc_filter

def has_repeated_elements(lst):
    for i in range(len(lst) - 1):
        if lst[i] == lst[i + 1]:
            return True
    return False

def sort_and_remove_neighbors(lst, lon_idx, lat_idx, jul_idx):
    # given a list of lists that has longitude at <lon_idx>, latitude at <lat_idx> and julian decimal day at <jul_idx>,
    # return the list sorted by longitude and latitude, with profiles at the same lon/lat and within 15 minutes of each other suppressed

    s = sorted(lst, key = operator.itemgetter(lon_idx, lat_idx))

    for i in range(len(s)-1,0,-1):
        if s[i][lon_idx] == s[i-1][lon_idx] and s[i][lat_idx] == s[i-1][lat_idx] and abs(s[i][jul_idx] - s[i-1][jul_idx]) < 15.0/1440.0:
            del s[i]

    return s

def mask_far_interps(measured_pressures, interp_levels, interp_values, radius=15):
    # mask interpolated values that are more than <radius> dbar from the nearest measured pressure

    for i, level in enumerate(interp_levels):
        closest = min(measured_pressures, key=lambda x: abs(x - level))
        if abs(closest - level) > radius:
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
