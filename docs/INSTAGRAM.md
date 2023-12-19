# Instagram detection

`InstagramProcessor` uses the shared frame reader and exporter. Its icon rule
looks for the heart, comment and share templates.

## Prepare the frame

At an analysis height of 960 pixels, retain pixels whose three BGR channels are
each in `[230, 255]`. Convert to grayscale, apply a 2-by-2 elliptical closing
operation, and fill contours with area greater than 50 pixels.

## Match icons and test their positions

Normalized template correlation must be at least 0.85. The matcher returns the
first qualifying top-left coordinate with `x > 360`, rather than the strongest
match. For any of the three icons, a boundary requires:

$$90 < y < 860, \qquad (y < 320\;\text{or}\;y > 960-960/6.3),$$

and a time gap strictly greater than 0.4 seconds since the last accepted cut.
This is a position test on the current frame; it does not track icon motion.

An accepted icon boundary produces `part_N_reel.mp4` and advances the shared
segment start and counter.
