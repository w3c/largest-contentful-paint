# Largest Contentful Paint Explainer



## Objectives

Developers today don't have a reliable metric that correlated with their user's visual rendering experience. Existing metrics such as First Paint and First Contentful Paint focus on initial rendering, but don't take into account the importance of the painted content, and therefore may indicate times in which the user still does not consider the page useful.

Largest Contentful Paint (LCP) aims to be a new page-load metric that better correlates with user experience than the existing page-load metrics, and is easy to understand and reason about.

At the same time, LCP does not try to be respresentative of the user's entire rendering journey. That's something that the lower-level [Element-Timing](https://wicg.github.io/element-timing/) can help developers accomplish.


## What is Largest Contentful Paint 

Largest Contentful Paint (LCP) is a new page load metric, which describes page speed as the speed of delivering the largest contentful element to the screen.

It is the high-level metric, where [Element Timing](https://github.com/WICG/Element-Timing) is its low-level primitive, aiming to provide a meaningful result even for developers that won't go through the trouble of annotating their sites. 


### Why largest and contentful 

In order to better correlate with user experience, we designed LCP to represent the speed of delivering **main content** on screen. While the main content is important to the user experience, what is the main content is highly subjective and different users can come up with different answers. As an approximation, LCP uses the largest contentful element to represent the main content.

Historically, we’ve tried [complex heuristics](https://docs.google.com/document/d/1BR94tJdZLsin5poeet0XoTW60M0SjvOJQttKT-JK8HI) to determine when the page has meaningfully painted, as in First Meaningful Paint (FMP) metric. In practice, these heuristics have been able to work well for ~80% of content, but often produce strange, hard-to-explain outlier results in the remaining cases. LCP is a simple, practical approach to estimating a time that represents a meaningful paint for users, without heavily relying on complex heuristics. With LCP, we don’t observe the outliers encountered with FMP.


### Largest: biggest initial size

LCP uses the largest element to approximate the main content on the page. As [visual sizes](#visual-size) of elements can change during the whole page load, LCP uses the size of the [first paint](#paint-first-paint) of elements to decide which one is the largest. During the page load, an element can be painted many times, for example, the first paint when an element has just been added to the DOM tree, the repaint when text has to replace its font with the newly loaded web font. An element can even be removed from the DOM, and reattached later. No matter how many times an element is painted, the metric uses the size of the first paint to decide the largest.

The use of **initial** size affects pages where the elements move, such as animated image carousel. In such carousel examples, for images that are initially outside the viewport and that "slide" into it, LCP may define their size as their painted size when they are first added to the DOM, which will be 0. The same issue also applies to interstitials or dialog boxes that slide into the viewport.


### Contentful: text, image, background images, videos’ poster-images 

The contentful elements in LCP’s context include two main groups - textual and pictorial.

Groups of text nodes are created as described in the <a href="https://github.com/WICG/element-timing#text-considerations">text considerations section</a> of the Element Timing explainer. The textual nodes which are grouped includes:

*   text nodes
*   SVG text nodes

Pictorial elements are described in the <a href="https://github.com/WICG/element-timing#image-considerations">image considerations section</a> of the Element Timing explainer. The pictorial elements includes:

*   image elements
*   html elements with [contentful](#contentful-style-background-images) style-background-images
*   video elements with poster images

In the future, we may add canvas and video elements that paint their initial frame to the contentful elements group.


#### Contentful style-background-images 

Background images can serve a role as background or as part of the contents of the page. LCP uses heuristics to distinguish between those uses and exclude one with a background role, as they are less relevant to user experience than those used as content.

The heuristics to identify a background-purposed image may include:
* Document position - Background images of the document's `<body>` or its `<html>` are more likely to serve as a background for the page.
* Background image that's not fetched - a CSS background images that's either a [cross fade](https://drafts.csswg.org/css-images-4/#funcdef-cross-fade) or a [gradient](https://drafts.csswg.org/css-images-4/#typedef-gradient).

### Paint: first paint 

We have different definitions of first paint time for textual and pictorial elements. For pictorial elements in particular, the first paint time refers to the first paint after the image is fully loaded and decoded. For text, the first paint time is the first paint of the text at its earliest font. In other words, if a text element with a default font is repainted after its web-font is loaded, the first paint time refers to that of the default font.


### Visual size 

In the context of LCP, the size of an element refers to the visual size, which is the size visible to users. In terms of visibility, the metric has included the following factors:



*   The visible area of an element is clipped by the screen viewport, frame viewports, ancestor elements’ visible area.
*   Elements whose CSS visibility property set to “hidden” is regarded as invisible.
*   A text element in [font-block period](https://developer.mozilla.org/en-US/docs/Web/CSS/@font-face/font-display#The_font_display_timeline) is invisible.

Note that occlusion is not taken into account due to implementation efficiency concerns. It may be added in the future if those concerns are alleviated.

Regarding text, there is some discrepency between the way users may preceive blocks of text and the way text is defined in the DOM tree.
While users tend to regard a paragraph as a block of text, the paragraph may be represented by several text nodes on the DOM tree because of links and different text style.
Currently LCP regards each text node as a unit of text, which is sometimes different from user perception.

The issue of grouping text nodes seems like an issue shared between LCP and its underlying primitive, Element Timing. Element Timing is exploring [grouping text nodes by their immediate parent](https://docs.google.com/document/d/1xhPJnXf0Nqsi8cBFrlzBuHavirOVZBd8TqdD_OyrDGw/edit#heading=h.1e3yk3amx58m).


### Interaction with user input 

The design of the metric has also considered the fact that user inputs may cause pages to show different content. Because of different ways users may interact with the page, the same page may produce different LCPs.

We observe that, for many pages, large elements can be inserted into the document in response to user input. Without ignoring updates after user input, LCP often reported values closer to the total time a user spent on the page. Without filtering out updates due to user input, LCP ends up measuring time to user input that inserted the largest element, rather than time until the main content of the page is initially visible.

In order to reduce this variation, the LCP algorithm only observe the page until users provide the first input. The first input includes all but the following types:



*   Mouse move/enter/leave
*   Pinch gesture


### The last candidate

During a page load, with page content constantly changing, LCP may have a different result at different times. The LCP algorithm keeps updating the LCP candidate until the ending condition is met. The ending condition can be each of these:

*   the user provides the first input
*   the page navigates away

It’s possible that the last candidate returned would be a premature result, because the measurement was aborted (due to the user navigating away or due to [user input](https://docs.google.com/document/d/1ySnglZJiCbOrOMX8PNgE0mRKmt9vglNDyggE8oYN8gQ/edit?disco=AAAACm_mTEg&usp_dm=false&ts=5c8a36c5#heading=h.leq0znnz6i6w)). This will cause a skew in the result because the result haven’t considered the content loaded (or that would have been loaded) after its termination. This ‘abort bias’ is inherent to any metric that is conditionally recorded only if the page visit reaches the point in time where the metric is observed. While a single sample may be affected by abort bias, aggregating a large number of samples can mitigate this problem. We find that using aggregate statistics for higher percentiles, such as 90th, avoids bias due to these early aborts.


### Ignore removed elements

In order to avoid considering  ephemereal elements (such as splash screens) as the largest contentful paint, LCP ignores removed elements. If a content element is removed from the DOM tree, the element is temporarily excluded from being an LCP candidate.

## API shape
One challenge with exposing LCP as a Performance Entry is the fact that the browser is not aware of the "winning" candidate until the measurement is over, at which point it is potentially too late, as the user may have navigated away.
As such, we want to make sure that the latest candidate is exposed to developers as the page is loaded, and analytics scripts can pick up that latest candidate at each point in time.

For that purpose we want to satisfy a few, somewhat contradictory, requirements:

* Developers need to be able to always pick the latest candidate.
* Developers need to be notified when the candidate value changes.
* Accumulating all potential candidates should not take an excessive amount of memory.
* The API should be consistent with other performance APIs.

We chose to use the `PerformanceObserver` API, define a `LargestContentfulPaint` performance entry, and dispatch a new entry for each new candidate element (for which there can be one per paint operation), while leaving older ones in place.

That approach has the advantage of enabling developers to pick the latest candidate, notifying them of new candidates, and being consistent with other performance APIs.
Its main disadvantage is that it accumulates all the entries, resulting in suboptimal memory consumption. But as mentioned, the number of candidates is capped by the number of paint operations, and in practice is expected to be significantly lower than that.

### Example code
```javascript
const po = new PerformanceObserver(list => {
    const entries = list.getEntries();
    const entry = entries[entries.length - 1];
    // Process entry as the latest LCP candidate
    let accurateLCP = false;
    // Use renderTime if it is nonzero. In this case, LCP will be accurate.
    if (entry.renderTime) {
      accurateLCP = true;
      largestPaintTime = entry.renderTime;
    }
    // If not present, use loadTime. In this case, LCP will be less accurate.
    else {
      // Try to avoid getting here by adding Timing-Allow-Origin headers!
      largestPaintTime = entry.loadTime;
    }
    // Send the LCP information for processing.
});
po.observe({entryTypes: ['largest-contentful-paint']});
```

### Alternatives explored

#### `PerformanceObserver` + entries while deleting older entries
A similar option to the above that would avoid the extra memory consumption is for the browser to dispatch a `PerformanceEntry` for each candidate, but only keep a reference to the last one.

Advantages: Enables developers to pick the latest candidate, notifies them, and doesn't result in a lot of memory usage.
Disadvantage: inconsistent with other performance APIs.

#### `performance.LatestContentfulPaint()` method
Here, we would mint a new method that developers can poll in order to get the latest LCP candidate.

Advantages: Enables developers to pick the latest candidate, and does not accumulate extra entries.
Disadvantage: Does not notify developers when the candidate is replaced, requiring polling based solutions. Not consistent with other performance APIs.

## LCP compared to other metrics

### Advantages

While FCP focuses on the speed of delivering the first paint, LCP focuses on the speed of delivering main content. As a proxy for main content, the largest element won’t always identify the main content perfectly, but in practice we have found it to be a simple heuristic that works well in most cases.

Compared to FCP, LCP includes an important factor related to the user experience - the element’s visual size. As FCP does not consider whether elements are painted out of viewport, it may choose a paint that’s out of users’ awareness to represent page speed. As FCP does not consider the size of content, it may choose a trivial element appearing significantly earlier than the main content, for which users come to the page, to represent page speed. LCP improves on FCP for identifying time to main content

LCP is also aware of content removal. As FCP does not ignore removed content, it may choose the splash screen to represent page speed, while page content may appear much later. LCP excludes the splash screen after the splash screen is removed from page, so that it can target the page content that users care about to represent page speed. 

Compared with FMP which relies on [complex heuristics](https://docs.google.com/document/d/1BR94tJdZLsin5poeet0XoTW60M0SjvOJQttKT-JK8HI/edit), LCP uses simpler heuristics, which makes its results easier to interpret.


### Limitations

As heuristics for other metrics have shortcomings, some of the heuristics that LCP uses are not perfect as well. It can perform poorly for certain scenarios.

* LCP tries to [exclude](#contentful-style-background-images) non-content background-images. The heuristics LCP uses cannot rule out all backgroundful images. If a non-content background-image is not attached to the document, the image won’t be excluded, and the largest element may not be the main content that LCP intends to capture.

* LCP is deactivated after user input. If main content shows up after any user input, then the largest element that LCP uses won’t reflect the main content.
* Complex UI structures such as image carousels may be mis-represented by LCP. Since the element's first paint is the one taken into account, images that are painted outside the viewport and slide in will be ignored. Similarly, images painted in the viewport but that then slide out of it will be ignored as well.

# Security & privacy considerations

This API relies on Element Timing for its underlying primitives. LCP may expose some element not exposed by Element Timing in case that they are smaller than Element Timing's limits, but are still the largest elements to be painted up until that point in the page's loading. That does not seem to expose any sensitive information beyond what Element Timing already enables.

## Acknowledgements

This explainer is based on a [document](https://docs.google.com/document/d/1ySnglZJiCbOrOMX8PNgE0mRKmt9vglNDyggE8oYN8gQ/edit#) by Liquan (Max) Gu, Bryan McQuade, and Tim Dresser, with inputs from Steve Kobes, Xianzhu Wang, and Nicolás Peña Moreno.

