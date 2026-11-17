# Computing Largest Contentful Paint from LCP entries

[Largest Contentful Paint (LCP)](https://web.dev/articles/lcp) is the time the largest content in the viewport painted during a page load.
The [specification](https://w3c.github.io/largest-contentful-paint/) and the [explainer](README.md) already cover the entries.
This doc is about the rest: what time to measure from, and which page loads to count.
It doesn't add anything to the specification.

The choices here follow what [web-vitals](https://github.com/GoogleChrome/web-vitals/blob/main/src/onLCP.ts) does today.
They are heuristics, so they can change over time.

## The basic value

For a page loaded in the foreground, LCP is the `startTime` of the latest `largest-contentful-paint` entry.
The browser stops reporting new entries after the first input or scroll, so the latest entry by then is the final value.
If no entry arrives, there is no LCP value, which is not the same as an LCP of zero.

`startTime` is relative to `performance.timeOrigin`, the start of the navigation.
That is the right starting point only when the page loaded in the foreground, without prerendering and without a back-forward cache restoration.
The sections below cover the other cases.

## Prerendered pages

A prerendered page can paint its largest content before the user sees the page.
Measure from activation instead of navigation start.
Subtract [`activationStart`](https://wicg.github.io/nav-speculation/prerendering.html#dom-performancenavigationtiming-activationstart) from the navigation timing entry, and clamp the result at zero, because the content can paint before activation.
`activationStart` is zero for a page that was not prerendered, so the same calculation works for every load.
web-vitals waits for the `prerenderingchange` event before it starts observing a prerendered page.

## Pages loaded in the background

A page opened in a background tab paints while the user is not looking at it.
The specification's [limitations](https://w3c.github.io/largest-contentful-paint/#limitations) section notes that these loads report larger values than expected.
web-vitals does not report LCP for these loads.
It ignores any entry whose render time is later than the first time the page was hidden.
A page that is already hidden when the code runs is treated as hidden from the start.
Where the browser supports `visibility-state` entries, web-vitals reads the first hidden time from them, which also covers a hidden period before the code ran.

Measuring from the first time the page became visible is a possible alternative, but web-vitals does not do this.

## Back-forward cache restorations

A page restored from the back-forward cache gets no new `largest-contentful-paint` entries, because the API follows document loads.
To report a value for the restore, web-vitals starts from the `timeStamp` of the `pageshow` event with `persisted` set to `true`.
It waits two animation frames and reports `performance.now()` minus that time stamp.
This measures the time to the next frame after the restore, not the paint of the largest content.

## Soft navigations

The [Soft Navigations proposal](https://github.com/WICG/soft-navigations) is experimental.
It adds `soft-navigation` entries and `interaction-contentful-paint` entries.
Each `interaction-contentful-paint` entry carries a `largestContentfulPaint` for the content painted after an interaction, which gives a "soft LCP" for each soft navigation.
A `soft-navigation` entry also returns the largest of these through `getLargestInteractionContentfulPaint()`.

When soft navigation reporting is turned on, web-vitals starts a new LCP value for each `soft-navigation` entry.
It only uses `interaction-contentful-paint` entries whose `interactionId` matches that soft navigation.
The value is the `renderTime` of the entry's `largestContentfulPaint` minus the `startTime` of the `interaction-contentful-paint` entry.

## Example

This example handles prerendered pages and pages hidden before their content painted.
It does not handle back-forward cache restorations or soft navigations.

```js
function onActivated(callback) {
    if (document.prerendering) {
        addEventListener('prerenderingchange', callback, { once: true });
    } else {
        callback();
    }
}

onActivated(() => {
    const navigation = performance.getEntriesByType('navigation')[0];
    const activationStart = navigation?.activationStart ?? 0;
    let firstHiddenTime = document.visibilityState === 'hidden' ? 0 : Infinity;

    addEventListener('visibilitychange', event => {
        if (document.visibilityState === 'hidden') {
            firstHiddenTime = Math.min(firstHiddenTime, event.timeStamp);
        }
    }, true);

    let lcp;
    new PerformanceObserver(list => {
        for (const entry of list.getEntries()) {
            if (entry.startTime < firstHiddenTime) {
                lcp = Math.max(entry.startTime - activationStart, 0);
            }
        }
    }).observe({ type: 'largest-contentful-paint', buffered: true });
});
```

`lcp` stays `undefined` until an entry counts, and stays `undefined` for a page that was hidden from the start.
Before reporting, process any entries returned by the observer's `takeRecords()` the same way.
This example only checks visibility from the time it runs.
Code that loads late can miss an earlier hidden period unless it reads `visibility-state` entries as web-vitals does.

## Further reading

- [Core Web Vitals LCP definition](https://web.dev/articles/lcp)
- [web-vitals LCP implementation](https://github.com/GoogleChrome/web-vitals/blob/main/src/onLCP.ts)
- [Soft Navigations proposal](https://github.com/WICG/soft-navigations)
