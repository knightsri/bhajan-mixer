# Bhajan Mixer - TODO & Enhancement Ideas

## Future Enhancements

### Audio/Video Output Options Enhancement
**Status:** Proposed
**Priority:** Low
**Description:**
Replace the current `--mp4out` flag with more explicit, easier-to-remember options:

**Current behavior:**
- Default: Audio only (MP3)
- `--mp4out`: Audio + Video (MP3 + MP4)

**Proposed behavior:**
- `--audio-only` (default): Process audio only (MP3)
- `--video-only`: Process video only (MP4) - skip audio processing
- `--both-audio-video` (or `--audio-and-video`): Process both audio and video

**Benefits:**
- More intuitive and self-documenting
- Easier to remember which flag does what
- Allows video-only processing (currently not possible)

**Implementation notes:**
- Maintain backward compatibility with `--mp4out` (deprecated but still functional)
- Ensure mutual exclusivity of the three new flags
- Update help text and documentation
- Add migration notes for users currently using `--mp4out`

---

## Completed Features

### Long MP3 Truncation Feature
**Completed:** 2025-11-17
**Description:**
Added ability to truncate long MP3 files during processing:
- `--LONG-MP3-MAX <minutes>`: Threshold for considering an MP3 "long"
- `--LONG-MP3-CUTOFF <minutes>`: Duration to keep from long MP3s (from the start)
- Both parameters must be provided together
- Only affects MP3 files, not MP4 (video) files
- Auto-adjusts cutoff if it exceeds max duration
