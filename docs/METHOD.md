# Method: interface cues to clip boundaries

This describes executable behavior in the processors. Some source comments and diagnostic print strings differ from the actual conditions; the conditions below follow the code.

## 1. Decode and normalize the analysis image

`VideoProcessor` opens the recording with both MoviePy and OpenCV. OpenCV provides FPS, frame count and dimensions. The estimated duration is `total_frames / fps`. Each decoded frame is resized to height $H=960$ and width $W=\lfloor960w/h\rfloor$, keeping its aspect ratio.

Only the analysis image is resized. Exports read the original input video through FFmpeg; they are not videos of the processed grayscale frames.

## 2. Isolate interface shapes

All three BGR channels must lie within the selected inclusive interval:

| Detector | BGR interval | Processing after masking |
| --- | --- | --- |
| Instagram Reels | `[230, 255]` in each channel | Grayscale, one closing operation with a 2-by-2 elliptical kernel, fill contours with area greater than 50 pixels. |
| TikTok | `[220, 255]` in each channel | Grayscale and the same closing operation; no contour filling. |
| Instagram feed | `[250, 255]` in each channel | Grayscale, closing, contour filling, two dilations, two erosions, white vertical border lines, inversion. |

These rules favor bright interface elements. Content pixels can also pass the mask.

## 3. Match the icon templates

For the Reels/TikTok branches, each template is matched with OpenCV's `TM_CCOEFF_NORMED`. In simplified notation, at image position $(x,y)$:

$$
R(x,y)=\frac{\sum_{u,v} T'(u,v)I'_{x,y}(u,v)}{\sqrt{\sum_{u,v}T'(u,v)^2\sum_{u,v}I'_{x,y}(u,v)^2}},
$$

where the primes indicate subtracting the template or image-window mean. The code accepts scores $R\ge0.85$.

The shared matcher returns the top-left $y$ coordinate of the **first** qualifying location with top-left $x>360$. It is not the highest-scoring location, an icon center or a tracked trajectory. `numpy.where` enumeration makes it the first qualifying position in array order. The matcher also draws white rectangles into the grayscale image before the next template is matched, so later matches see a modified image.

| Platform | Templates in matching order | Supplied width by height |
| --- | --- | --- |
| Instagram | Heart, comment, share | 27 x 23; 29 x 29; 25 x 21 pixels |
| TikTok | Heart, share, save | 40 x 34; 50 x 45; 31 x 35 pixels |

Template sizes do not adapt to interface scale. The PNGs are loaded as grayscale with OpenCV; alpha is not supplied as a template mask.

## 4. Apply boundary rules

For each frame the candidate time is:

$$ t=\frac{\mathrm{CAP\_PROP\_POS\_MSEC}}{1000}+\frac{1.5}{\mathrm{fps}}. $$

The icon branches require $t-s>0.4$ seconds, where $s$ is the previous accepted boundary, initially zero. Any one passing icon is sufficient.

| Rule | Vertical condition at analysis height 960 |
| --- | --- |
| Instagram heart, comment or share | $90<y<860$ and either $y<320$ or $y>807.619\ldots$. |
| TikTok heart | $y\le480$ or $y>807.619\ldots$. |
| TikTok share | $y\le600$ or $y>807.619\ldots$. |
| TikTok save | $y\le564.705\ldots$ or $y>807.619\ldots$. |

The high-position threshold is $H-H/6.3$. TikTok's low-position denominators are 2, 1.6 and 1.7. There is no requirement to see an icon move between two frames: the implementation tests location on each frame and then applies a minimum time gap.

The Instagram feed branch instead approximates contours with tolerance 4% of their perimeter. A contour must have four vertices, bounding-box width greater than $W-20$, top coordinate $45\le y\le120$, height $150\le h\le200$, and $t-s>1$ second.

Instagram calls its Reels branch first, then its feed branch on a copy of the same original frame. They share `start_time` and `part_counter`. A Reels boundary on that frame updates the start time before the feed rule runs, preventing the feed gap test from immediately passing.

## 5. Export and continue

An accepted boundary exports the interval from $s$ to $t$ from the original recording, increments the shared counter, and sets $s=t$. Processing then continues with later frames. At the first failed `cap.read()`, the base class exports a final interval to `total_frames / fps` and removes its input pathname.

The FFmpeg wrapper uses input-side `ss` and `to`, asks for AAC audio at 192 kb/s, and leaves the video codec to FFmpeg defaults. It does not specify stream copy. Do not describe the output as lossless or promise frame-exact cuts. Existing output paths are skipped without checking completeness.

## What the boundary represents

A boundary is an interface-rule trigger. It is a candidate change between feed items, not a verified post ID, natural shot boundary or semantic event. Over-splitting, missed transitions, bright content, different app layouts and timestamp irregularities remain empirical questions. A useful future evaluation would compare detected boundaries against manually annotated changes, including temporal tolerance, false positives and missed changes. No such evaluation is included in this source snapshot.
