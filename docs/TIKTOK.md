# TikTok detection

`TikTokProcessor` matches the heart, share and save templates. Each decoded
frame is resized to 960 pixels high before detection.

## Frame preparation

Retain pixels whose three BGR channels are each in `[220, 255]`, convert to
grayscale, and apply a 2-by-2 elliptical closing operation. This detector does
not fill contours.

## Boundary rules

Template correlation must be at least 0.85 and the qualifying match must have
top-left `x > 360`. The first qualifying match supplies the top-left `y`.

| Icon | Passing vertical position |
| --- | --- |
| Heart | $y\le480$ or $y>960-960/6.3$ |
| Share | $y\le600$ or $y>960-960/6.3$ |
| Save | $y\le960/1.7$ or $y>960-960/6.3$ |

Any passing icon can trigger a cut if the time since the last accepted cut is
strictly greater than 0.4 seconds. The code uses frame timestamp plus `1.5/fps`
as the candidate cut time.

Each accepted cut exports `part_N.mp4`, increments the counter, and moves the
segment start to the cut. A frame without an accepted cut leaves the start
unchanged. At the first failed frame read, the shared processor exports the
remaining interval to its estimated recording duration.
