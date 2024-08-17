import numpy as np

def detect_peaks(data, threshold, distance=1):
    """Detect peaks in a 1D array based on a threshold and minimum distance 
    between peaks.
    
    Parameters:
    data : array-like
        1D array of data to search for peaks.
    threshold : float
        Minimum value for a peak to be considered.
    distance : int, optional
        Minimum number of samples between consecutive peaks (default is 1).
    
    Returns:
    array-like
        Indices of the detected peaks.
    """
    peaks = np.where((data[1:-1] > data[:-2]) & (data[1:-1] > data[2:]) & (data[1:-1] > threshold))[0] + 1
    if distance > 1:
        filtered_peaks = []
        last_peak = -distance
        for peak in peaks:
            if peak - last_peak >= distance:
                filtered_peaks.append(peak)
                last_peak = peak
        peaks = np.array(filtered_peaks)
    
    return peaks

