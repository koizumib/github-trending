tag: v0.3.0
name: v0.3.0
published_at: 2026-04-15T02:04:44Z
prerelease: False

This release adds masks, a graph editor for keyframe curves, volume and speed controls, preview zoom, canvas backgrounds, stickers, and a lot more.

## Features
- Added a brand page with downloadable brand assets. Assets are also accessible directly from the header logo context menu.
- Scale now has separate width and height controls. You can stretch or squash elements independently on each axis.
- Volume control for audio and video elements, both in the properties panel and inline on timeline clips.
- Speed control for video and audio clips. Includes a maintain pitch option so audio doesn't chipmunk or deepen when you change the rate.
- Masks. Hide or reveal parts of any video or image layer. Choose from split, rectangle, ellipse, star, heart, diamond, and cinematic bars. Adjust position, size, rotation, feather, and stroke in the properties panel, or drag the handles in the preview.
- Canvas backgrounds are back. Set a blur, solid color, or gradient as the canvas background from the new Background tab in the settings panel.
- Custom canvas size. Instead of being locked to a handful of presets, you can now enter any width and height you want.
- Preview zoom and panning. Zoom into the canvas to work on fine details, and pan around to navigate when zoomed in.
- Stickers panel now has content. Browse and add logos, country flags, and shapes.
- You can now import transcript files to generate captions instead of running auto-transcription.
- Graph editor for keyframe curves. Shape the easing between keyframes by dragging bezier handles.
- Multiple selected timeline clips move and resize together.
- Position X and Y can now be animated independently.
- Keyframes can be copied and pasted between elements.
- Timeline clips can expand to show a lane for each animated property. Right-click a clip -> "Expand keyframes" to see all properties in their own rows.

## Improvements
- Added a changelog link to the footer.
- Playback performance is dramatically better. The editor used to slow to a crawl during playback, and audio would stutter when interacting with elements mid-play. Both are fixed.
- More vertical space between timeline tracks. Selection outlines on adjacent tracks no longer overlap each other.
- Holding Shift or Ctrl while drag-selecting in the timeline now adds to your existing selection instead of replacing it. Matches how Shift/Ctrl+click already worked.
- Timeline track rows now highlight when they contain a selected element, making it easier to see which tracks are active at a glance.
- System fonts (Arial, Helvetica, Times New Roman, and others) now appear in the font picker alongside Google Fonts.
- Your projects can disappear if your disk runs low on space. OpenCut now asks the browser to protect them.
- The properties panel has been redesigned with a tabbed layout.
- Audio waveforms have gotten an upgrade. The old ones were inaccurate, prone to crashing, and not very useful. The new ones are RMS-based, properly scaled, and only render what's visible so they don't slow things down.
- The timeline now opens scrolled to the bottom, so your main video track is visible right away instead of being hidden above the fold.
- The settings panel has been redesigned with a cleaner layout and better organization.
- You can now select multiple assets in the assets panel. Useful for deleting several at once.
- If your browser doesn't support GPU-accelerated rendering, the editor now shows a notice explaining why and suggests switching to another browser.

## Fixes
- Sponsor logos now correctly invert in dark mode.
- Media asset cards in the grid view were larger than their thumbnails, leaving empty space around each item. Cards now size to their content.
- Project thumbnails now generate correctly even when the timeline is empty. If you set a background color or gradient with no clips, the thumbnail reflects that instead of staying blank.
- Clicking a selected element no longer keeps the rest of the selection.
- Track labels on the left side of the timeline were misaligned with the tracks on the right.
- Clicking in the empty space below timeline tracks now seeks the playhead.
- Timeline vertical scroll now works anywhere in the panel, not just over the track labels. The header no longer scrolls with the tracks.
- MP4 exports with audio failed on Firefox. The export now completes successfully regardless of browser.
- Snap guides in the preview panel didn't show when moving a full-canvas element to the center of the frame.
- The rotation handle could float above the editor UI when an element was near the top of the canvas. It now clips to the preview area.
- Images with a blur effect at 0% intensity would disappear completely when a blurred background was also active. Now 0% blur correctly renders the image unchanged.
- Section titles in the properties panel showed the wrong text color when the section wasn't collapsible. Non-collapsible titles now use the correct muted style.
- Blur looked pixelated at higher intensities instead of producing a real blur. Both the canvas background blur and the blur effect are now fixed.
- Auto-generated captions were sometimes inaccurate. The underlying issue has been fixed.
- Text element handles no longer shift position as you type.
- The rotation handle drifted further and further from the element as the canvas size got smaller. On a 100x100 project it was almost off-screen. The gap is now a fixed size regardless of canvas dimensions or zoom.

<details>
<summary>Technical details</summary>

- Ripple editing now has a proper algorithmic foundation. The old inline approach was replaced with a diff-based system in `src/lib/ripple/`: track snapshots before and after an operation are compared as interval sets, vacated intervals are computed (accounting for elements moved to other tracks), and the result is a list of explicit `RippleAdjustment` values applied in a separate pass. Composable, testable, and independent of the command that triggered it.
- Time is now represented as `MediaTime`, an integer tick count at 120,000 ticks per second, defined in `rust/crates/time`. Previously, floating-point seconds were used throughout, which accumulated rounding errors and made frame alignment imprecise. 120,000 was chosen because it divides evenly by every standard frame rate denominator, including drop-frame rates: 23.976 maps to 5,005 ticks/frame, 29.97 to 4,004, 30 to 4,000. `FrameRate` is a rational `{numerator, denominator}` type rather than a float. All time arithmetic, frame snapping, and timecode formatting are implemented in Rust and exposed via WASM.
- Track ordering is now enforced at the type level. `SceneTracks` replaces a flat track array with three explicit fields: `overlay`, `main` (a singleton `VideoTrack`), and `audio`. The type makes it structurally impossible to mix track kinds or misplace a track.
- The WebGL renderer has been replaced with a Rust/wgpu compositor compiled to WASM. The `rust/` crate tree covers compositing (`rust/crates/compositor`), effects (`rust/crates/effects`), masks with JFA-based feathering (`rust/crates/masks`), GPU context (`rust/crates/gpu`), and time (`rust/crates/time`). WASM bindings live in `rust/wasm/` and are consumed from TypeScript through `src/lib/wasm/`. The old GLSL shaders and WebGL utilities are gone.
- `src/types/` and `src/constants/` have been dissolved. All types and constants now live alongside the code that owns them inside `src/lib/`. The `packages/env` and `packages/ui` internal packages were also folded into the web app, with icons at `src/components/icons/` and env at `src/lib/env/`.
- The web app can now deploy to Cloudflare Workers via OpenNext. `wrangler.jsonc` and `apps/web/open-next.config.ts` are included for anyone self-hosting.
- `apps/desktop/` is a new GPUI + Rust app. It is early: there is a `main.rs` and a working build setup, but no features yet.
- 16 new storage migration steps were adde