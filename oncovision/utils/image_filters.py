import numpy as np
import cupy as cp
import cv2


def adaptiveBilateralFilter(image, window_size=7, sigma_d=1.0):
    ''' Function that returns an image filtered with an adaptive bilateral filter.
    Parameters
    ___
    image: numpy array
        The input image to be filtered.
    window_size: int
        The size of the window used for filtering. It should be an odd number.
    sigma_d: float
        The constant used to calculate the domain filter. It controls the spatial extent of the filter.
    Returns
    ___
    filtered_image: numpy array
        The filtered image.
    '''
    image = cv2.normalize(image.astype(np.float32), None, 0, 1, cv2.NORM_MINMAX)
    pad = window_size // 2
    padded_image = cv2.copyMakeBorder(image, pad, pad, pad, pad, cv2.BORDER_REFLECT)
    filtered_image = np.zeros_like(image)

    # Create the domain filter
    x, y = np.meshgrid(np.arange(-pad, pad + 1), np.arange(-pad, pad + 1))
    domain_filter = np.exp(-(x**2 + y**2) / (2 * sigma_d**2))

    h, w = image.shape
    for i in range(h):
        for j in range(w):
            # Get the local window
            i1, j1 = i + pad, j + pad
            region = padded_image[i1 - pad : i1 + pad + 1, j1 - pad : j1 + pad + 1]
            center = padded_image[i1, j1]

            # ABF adaptive offset
            mean = np.mean(region)
            delta = center - mean
            if delta > 0:
                zeta = np.max(region) - center
            elif delta < 0:
                zeta = np.min(region) - center
            else:
                zeta = 0

            # Sigma for range filter using local standard deviation
            # Add a small value to avoid division by zero
            sigma_r = np.std(region) + 1e-6

            # Calculate the range filter
            diff = region - center - zeta
            range_filter = np.exp(-(diff ** 2) / (2 * sigma_r**2))

            # Combine the domain and range filters
            combined_filter = domain_filter * range_filter
            combined_filter /= np.sum(combined_filter)

            # Filter the region
            filtered_image[i, j] = np.sum(region * combined_filter)
    
    return (filtered_image * 255).astype(np.uint8)


def cudaAdaptiveBilateralFilter(image, window_size=7, sigma_d=1.0):
    ''' Function that returns an image filtered with an adaptive bilateral filter.
    Parameters
    ___
    image: numpy array
        The input image to be filtered.
    window_size: int
        The size of the window used for filtering. It should be an odd number.
    sigma_d: float
        The constant used to calculate the domain filter. It controls the spatial extent of the filter.
    Returns
    ___
    filtered_image: numpy array
        The filtered image.
    '''
    pad = window_size // 2
    img = cp.asarray(image, dtype=cp.float32) / 255.0
    img = cp.pad(img, pad, mode='reflect')
    H, W = image.shape
    k = window_size

    # Create strided sliding window view
    shape = (H, W, k, k)
    strides = img.strides * 2
    patches = cp.lib.stride_tricks.as_strided(img, shape=shape, strides=strides)

    # Domain filter
    y, x = cp.meshgrid(cp.arange(-pad, pad + 1), cp.arange(-pad, pad + 1))
    domain_filter = cp.exp(-(x**2 + y**2) / (2 * sigma_d**2))
    domain_filter = domain_filter[None, None, :, :]

    # Central pixels
    center = patches[:, :, pad, pad][:, :, None, None]

    # Local stats
    local_mean = cp.mean(patches, axis=(2, 3), keepdims=True)
    local_min = cp.min(patches, axis=(2, 3), keepdims=True)
    local_max = cp.max(patches, axis=(2, 3), keepdims=True)
    delta = center - local_mean

    # ζ adaptive offset
    zeta = cp.where(delta > 0, local_max - center,
           cp.where(delta < 0, local_min - center, 0.0))

    # σr: adaptive std dev
    sigma_r = cp.std(patches, axis=(2, 3), keepdims=True) + 1e-5

    # Range filter
    diff = patches - center - zeta
    range_filter = cp.exp(-(diff**2) / (2 * sigma_r**2))

    # Combined kernel
    kernel = domain_filter * range_filter
    kernel /= cp.sum(kernel, axis=(2, 3), keepdims=True)

    # Apply to image
    result = cp.sum(kernel * patches, axis=(2, 3))
    return cp.asnumpy((result * 255).clip(0, 255).astype(cp.uint8))
