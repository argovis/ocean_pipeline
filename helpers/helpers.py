import numpy, datetime, scipy.interpolate, scipy.integrate, math, operator, juliandate

def mljul(year, month, day, time):
    # compute something appropriate to interpret as matlab's julian day
    
    return juliandate.from_gregorian(year, month, day) + time/24

def remap_longitude(longitude):
    # map longitudes onto [20,380)

    if longitude < 20:
        return longitude+360
    else:
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

def interpolate_to_levels(row, var, levels, pressure_buffer=100.0, pressure_index_buffer=5):
    # interpolate <var> to <levels> using PCHIP interpolation
    # keep <pressure_buffer> dbar on either side of the ROI and <pressure_index_buffer> points in the pressure buffer margins, at least.

    try:
        # find indexes of ROI
        p_bracket = pad_bracket(row['pressure'], levels[0], levels[-1], pressure_buffer, pressure_index_buffer)

        # interpolate; don't extrapolate to levels outside of measurement range
        interp = scipy.interpolate.PchipInterpolator(row['pressure'][p_bracket[0]:p_bracket[1]+1], row[var][p_bracket[0]:p_bracket[1]+1], extrapolate=False)(levels)

        # if there wasn't a measured level within a certain radius of each level of interest, mask the interpolation at that level.
        interp = mask_far_interps(row['pressure'][p_bracket[0]:p_bracket[1]+1], levels, interp)
        
    except Exception as e:
        print(f'pchip interpolation failed at {var}, {row["juld"]}, {row["latitude"]}, {row["longitude"]}: {e}')
        interp = 0xDEADBEEF

    return interp

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
    print(variable, pressure, low_i, high_i)
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

    return t_filter, s_filter, p_filter    

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

def integration_regions(regions, pressure, variable):
    # perform intrgation of <variable> over <pressure> for a list of <regions> specified as tuples of (low_roi, high_roi)

    integrals = []
    for region in regions:
        low_roi, high_roi = region
        integrals.append(integrate_roi(pressure, variable, low_roi, high_roi))

    return integrals

def integration_comb(regions, spacing=0.2):
    # generates a level spectrum with <spacing> levels populating the regions in <regions>.

    pressure = []

    for region in regions:
        low_roi, high_roi = region
        pressure.extend(numpy.arange(low_roi, high_roi+spacing, spacing))
    
    return numpy.round(pressure, 6)