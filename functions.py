import platform


# Linear interpolation
def interp(x_arr, y_arr, x):
    for i, xi in enumerate(x_arr):
        if xi >= x:
            break
    else:
        return y_arr[-1]

    x_min = x_arr[i - 1]
    y_min = y_arr[i - 1]
    y_max = y_arr[i]
    factor = (x - x_min) / (xi - x_min)
    return y_min + (y_max - y_min) * factor


# Get the serial number of CPU
def getserial():
    cpuserial = "0000000000000000"
    try:
        if platform.system() == 'Windows':
            # Extract serial from wmic command
            from subprocess import check_output
            cpuserial = check_output('wmic cpu get ProcessorId').decode().split('\n')[1].strip()
        else:
            # Extract serial from cpuinfo file
            f = open('/proc/cpuinfo', 'r')
            for line in f:
                if line[0:6] == 'Serial':
                    cpuserial = line[10:26]
            f.close()
    except:
        cpuserial = "ERROR000000000"

    return cpuserial
