# Largest Contentful Paint Explainer



## Objectives

Developers today don't have a reliable metric that correlates with their user's visual rendering experience. Existing metrics such as First Paint and First Contentful Paint focus on initial rendering, but don't take into account the importance of the painted content. Therefore, these metrics may indicate times in which the user still does not consider the page useful.

Largest Contentful Paint (LCP) aims to be a new page-load metric that correlates with user experience better than the existing page-load metrics, and is easy to understand and reason about.

At the same time, LCP does not try to be respresentative of the user's entire rendering journey. That's something that the lower-level [Element-Timing](https://wicg.github.io/element-timing/) can help developers accomplish.


## What is Largest Contentful Paint 

Largest Contentful Paint (LCP) is a new page load metric which describes the speed of delivering the largest contentful element to the screen.

LCP is the high-level metric, with [Element Timing](https://github.com/WICG/Element-Timing) being its low-level primitive. LCP aims to provide a meaningful result even for developers that won't go through the trouble of annotating their sites, which is a requirement to use Element Timing. 


### Why largest and contentful 

In order to better correlate with user experience, we designed LCP to represent the speed of delivering **main content** on the screen. While the main content is important to the user experience, what the main content is is highly subjective and different users can come up with different answers. As an approximation, LCP uses the largest contentful element to represent the main content.

Historically, we’ve tried complex heuristics to determine when the page has meaningfully painted, as in [First Meaningful Paint](https://docs.google.com/document/d/1BR94tJdZLsin5poeet0XoTW60M0SjvOJQttKT-JK8HI) (FMP) metric. In practice, these heuristics have worked well for ~80% of the content. But they often produce strange, hard-to-explain outlier results in the remaining cases. LCP is a simple, practical approach to estimating a time that represents a meaningful paint for users, without heavily relying on complex heuristics. With LCP, we don’t observe the outliers encountered with FMP.


### Largest: biggest initial size

LCP uses the largest element to approximate the main content on the page. As [visual sizes](#visual-size) of elements can change during the whole page load, LCP uses the size of the [first paint](#paint-first-paint) of elements to decide which one is the largest. During the page load, an element can be painted many times, for example, an element could be first painted when added to the DOM tree, and repainted when text has to replace its font with a newly loaded web font.

The use of **initial** size affects pages where the elements move, such as animated image carousels. In such carousels, for images that are initially outside the viewport and that "slide" into it, LCP may define their size as their painted size when they are first added to the DOM, which will be 0. The same issue also applies to interstitials or dialog boxes that slide into the viewport.


### Contentful: text, image, background images, videos’ poster-images 

The contentful elements in LCP’s context include two main groups - textual and pictorial.

Groups of text nodes are created as described in the <a href="https://github.com/WICG/element-timing#text-considerations">text considerations section</a> of the Element Timing explainer. The textual nodes which are grouped include:

*   text nodes
*   SVG text nodes

Pictorial elements are described in the <a href="https://github.com/WICG/element-timing#image-considerations">image considerations section</a> of the Element Timing explainer. The pictorial elements include:

*   image elements
*   html elements with [contentful](#contentful-style-background-images) style-background-images
*   video elements with poster images

In the future, we may add canvas and video elements to the group of contentful elements.


#### Contentful style-background-images 

Background images can serve a role as background or as part of the contents of the page. LCP uses simple heuristics to exclude background images with a background role, as they are less relevant to user experience than those used as content of the page.

The heuristics to identify a background-purposed image may include:
* Document position - background images of the document's `<body>` or its `<html>` are more likely to serve as a background for the page.
* Background image that's not fetched - a CSS background image that's either a [cross fade](https://drafts.csswg.org/css-images-4/#funcdef-cross-fade) or a [gradient](https://drafts.csswg.org/css-images-4/#typedef-gradient) is considered background for the page.

### Paint: first paint 

We have different definitions of first paint time for textual and pictorial elements. For pictorial elements, the first paint time refers to the first paint after the image is fully loaded. For text, the first paint time is the first paint of the text at its earliest font. In other words, if a text element with a default font is repainted after its web-font is loaded, the first paint time refers to that of the default font.


### Visual size 

In the context of LCP, the size of an element refers to the visual size, which is the size visible to users. In terms of visibility, the metric has included the following factors:

*   The visible area of an element is clipped by the screen viewport, frame viewports, and ancestor elements’ visible area.
*   An element whose CSS visibility property is set to “hidden” is regarded as invisible.
*   A text element in [font-block period](https://developer.mozilla.org/en-US/docs/Web/CSS/@font-face/font-display#The_font_display_timeline) is invisible.

Note that occlusion is not taken into account due to implementation efficiency concerns. It may be added in the future if those concerns are alleviated.

### Image instrinsic size

Sometimes, small images may be scaled to fit a larger portion of the viewport. This is usually the case for background images which do not represent key content of the website but still occupy a large portion of it. To address this problem, we have a heuristic to penalize the size of certain images. The formula is as follows:

```
image_size = visual_size * min(display_size, intrinsic_size) / display_size
```
`image_size` is the size of the image, as considered by the LCP algorithm. It is computed from the `visual_size`, the screen size occupied by the image. It is penalized when the `intrinsic_size` of the image is lower than its `display_size`, i.e., when the image has been stretched to occupy a larger portion of the viewport than the number of pixels it encodes.


### Interaction with user input 

The design of the metric has also considered the fact that user inputs may cause pages to show different content. Because of different ways users may interact with the page, the same page may produce different LCPs.

We observe that, for many pages, large elements can be inserted into the document in response to user input. Without ignoring updates after user input, LCP would often report values closer to the total time a user spent on the page. Without filtering out updates due to user input, LCP would often measure time to user input that inserted the largest element, rather than time until the main content of the page is initially visible.

In order to reduce this variation, the LCP algorithm only observes the page until users provide the first input. The first input includes all but the following types:

*   Mouse move/enter/leave
*   Pinch gesture


### The last candidate

During a page load, with page content constantly changing, LCP may have a different results at different times. The LCP algorithm keeps updating the LCP candidate until the ending condition is met. The ending condition can be each of these:

*   the user provides the first input as defined above
*   the page navigates away

It’s possible that the last candidate returned would be a premature result, because the measurement was aborted (due to the user navigating away or due to user input. This will cause a skew in the results due to elements that load after the algorithm terminates. This ‘abort bias’ is inherent to any metric that is conditionally recorded only if the page visit reaches the point in time where the metric is observed. While a single sample may be affected by abort bias, aggregating a large number of samples can mitigate this problem. We find that using aggregate statistics for higher percentiles, such as 90th, avoids bias due to these early aborts.


### Ignore removed elements

In order to avoid considering  ephemeral elements (such as splash screens) as the largest contentful paint, LCP ignores removed elements. If a content element is removed from the DOM tree, the element is excluded from being an LCP candidate.

## API shape

One challenge with exposing LCP as a [PerformanceEntry](https://w3c.github.io/performance-timeline/#the-performanceentry-interface) is the fact that the browser is not aware of the "winning" candidate until the measurement is over, at which point it is potentially too late, as the user may have navigated away.
As such, we want to make sure that the latest candidate is exposed to developers as the page is loaded, and analytics scripts can pick up that latest candidate at each point in time.

For that purpose we want to satisfy a few, somewhat contradictory, requirements:

* Developers need to be able to always pick the latest candidate.
* Developers need to be notified when the candidate value changes.
* Accumulating all potential candidates should not take an excessive amount of memory.
* The API should be consistent with other performance APIs.

We chose to use the [PerformanceObserver](https://w3c.github.io/performance-timeline/#the-performanceobserver-interface) API, define a `LargestContentfulPaint` entry, and dispatch a new entry for each new candidate element. This candidate is updated at most once per paint to avoid spamming entries and make computations more efficient.

This approach has the advantage of enabling developers to pick the latest candidate, notifying them of new candidates, and being consistent with other performance APIs.
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

Advantages: enables developers to pick the latest candidate, notifies them, and doesn't result in a lot of memory usage.

Disadvantage: inconsistent with other performance APIs.

#### `performance.LatestContentfulPaint()` method
Here, we would mint a new method that developers can poll in order to get the latest LCP candidate.

Advantages: enables developers to pick the latest candidate, and does not accumulate additional entries.

Disadvantages: does not notify developers when the candidate is replaced, requiring polling based solutions. Not consistent with other performance APIs.

## LCP compared to other metrics

### Advantages

While FCP focuses on the speed of delivering the first paint, LCP focuses on the speed of delivering main content. As a proxy for main content, the largest element won’t always identify the main content perfectly, but in practice we have found it to be a simple heuristic that works well in most cases.

Compared to FCP, LCP includes an important factor related to the user experience - the element’s visual size. As FCP does not consider whether elements are painted out of viewport, it may choose a paint that’s out of users’ awareness to represent page speed. In addition, FCP may be triggered by a trivial element appearing significantly earlier than the main content. LCP improves on FCP for identifying time to the main (largest) content.

LCP is also aware of content removal. As FCP does not ignore removed content, it may choose a splash screen to represent page speed, while page content may appear much later. LCP excludes the splash screen after the splash screen is removed from page, so that it can target the page content that users care about to represent page speed. 

Compared with FMP which relies on [complex heuristics](https://docs.google.com/document/d/1BR94tJdZLsin5poeet0XoTW60M0SjvOJQttKT-JK8HI/edit), LCP uses simpler heuristics, which makes its results easier to interpret and easier for various browser vendors to implement.


### Limitations

As heuristics for other metrics have shortcomings, some of the heuristics that LCP uses are not perfect as well. It can perform poorly for certain scenarios.

* LCP tries to [exclude](#contentful-style-background-images) background images that are not considered contentful. The heuristics LCP uses cannot rule out all background images that a user would consider unimportant. If an unimportant background image is not attached to the document, the image won’t be excluded, and the largest element may not be the main content that LCP intends to capture.

* LCP is deactivated after user input. If main content shows up after any user input, then the largest element that LCP uses won’t reflect the main content.

* Complex UI structures such as image carousels may be mis-represented by LCP. Since the element's first paint is the one taken into account, images that are painted outside the viewport and slide in will be ignored. Images painted in the viewport but that then slide out will be considered.

# Security & privacy considerations

This API relies on Element Timing for its underlying primitives. It does not seem to expose any sensitive information beyond what Element Timing already enables.

## Acknowledgements

This explainer is based on a [document](https://docs.google.com/document/d/1ySnglZJiCbOrOMX8PNgE0mRKmt9vglNDyggE8oYN8gQ/edit#) by Liquan (Max) Gu, Bryan McQuade, and Tim Dresser, with inputs from Steve Kobes, Xianzhu Wang, and Nicolás Peña Moreno.

