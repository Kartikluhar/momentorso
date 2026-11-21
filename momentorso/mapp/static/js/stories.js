/**
 * Momentorso Instagram-Style Stories Component & Viewer
 * Handles horizontal story bar, modal viewer, smooth auto-progression,
 * pause/resume on press, keyboard/touch navigation, and 24h backend expiration sync.
 */

(function () {
  'use strict';

  // State
  let stories = [];
  let currentIndex = 0;
  let isViewerOpen = false;
  let isPaused = false;
  let storyDuration = 5000; // 5 seconds per story
  let animFrameId = null;
  let progressStartTime = 0;
  let progressElapsedBeforePause = 0;
  let isImageLoaded = false;
  let isPointerDown = false;

  // Touch gesture state
  let touchStartX = 0;
  let touchStartY = 0;
  let touchStartTime = 0;

  // DOM Elements
  let container, listEl, viewerModal, progressBarContainer, viewerImage, viewerAmbientBg;
  let viewerLoader, viewerTitle, viewerCategory, viewerTimeAgo, viewerDescription, viewerCaptionBox;
  let closeBtn, pauseBtn, pauseIcon, prevBtn, nextBtn, tapZoneLeft, tapZoneRight;

  function init() {
    container = document.getElementById('storiesContainer');
    listEl = document.getElementById('storiesList');
    viewerModal = document.getElementById('storyViewerModal');

    if (!container || !listEl || !viewerModal) return;

    // Cache viewer elements
    progressBarContainer = document.getElementById('viewerProgressBars');
    viewerImage = document.getElementById('viewerImage');
    viewerAmbientBg = document.getElementById('viewerAmbientBg');
    viewerLoader = document.getElementById('viewerLoader');
    viewerTitle = document.getElementById('viewerTitle');
    viewerCategory = document.getElementById('viewerCategory');
    viewerTimeAgo = document.getElementById('viewerTimeAgo');
    viewerDescription = document.getElementById('viewerDescription');
    viewerCaptionBox = document.getElementById('viewerCaptionBox');

    closeBtn = document.getElementById('viewerCloseBtn');
    pauseBtn = document.getElementById('viewerPauseBtn');
    pauseIcon = document.getElementById('viewerPauseIcon');
    prevBtn = document.getElementById('viewerPrevBtn');
    nextBtn = document.getElementById('viewerNextBtn');
    tapZoneLeft = document.getElementById('viewerTapLeft');
    tapZoneRight = document.getElementById('viewerTapRight');

    // Load initial stories from server embedded JSON if available, or fetch
    const embeddedData = document.getElementById('initialStoriesData');
    if (embeddedData) {
      try {
        stories = JSON.parse(embeddedData.textContent || '[]');
      } catch (e) {
        console.error('Error parsing initial stories data', e);
        stories = [];
      }
    }

    if (stories.length === 0) {
      fetchStories();
    } else {
      renderThumbnails();
    }

    setupEventListeners();

    // Check expiration every 15 seconds to ensure expired stories vanish in real-time
    setInterval(checkExpiredStories, 15000);
    // Poll API every 45 seconds to catch newly published stories
    setInterval(fetchStories, 45000);
  }

  function fetchStories() {
    fetch('/api/stories/', { cache: 'no-store' })
      .then(res => res.json())
      .then(data => {
        if (data && Array.isArray(data.stories)) {
          stories = data.stories;
          renderThumbnails();
          if (isViewerOpen) {
            // Verify if current story is still in the active list
            if (currentIndex >= stories.length) {
              closeViewer();
            } else {
              renderProgressBars();
            }
          }
        }
      })
      .catch(err => {
        console.warn('Could not fetch active stories:', err);
      });
  }

  function checkExpiredStories() {
    if (!stories || stories.length === 0) return;
    const now = Date.now();
    const originalLength = stories.length;
    stories = stories.filter(story => {
      if (!story.expires_at) return false;
      const expireTime = new Date(story.expires_at).getTime();
      return expireTime > now;
    });

    if (stories.length !== originalLength) {
      renderThumbnails();
      if (isViewerOpen) {
        if (stories.length === 0) {
          closeViewer();
        } else if (currentIndex >= stories.length) {
          openStory(stories.length - 1);
        } else {
          renderProgressBars();
        }
      }
    }
  }

  function renderThumbnails() {
    if (!container || !listEl) return;

    // Filter out expired stories on client side
    const now = Date.now();
    stories = stories.filter(s => {
      if (!s.expires_at) return true;
      return new Date(s.expires_at).getTime() > now;
    });

    if (stories.length === 0) {
      container.classList.add('hidden');
      return;
    }

    container.classList.remove('hidden');
    listEl.innerHTML = '';

    stories.forEach((story, idx) => {
      const item = document.createElement('div');
      item.className = 'story-item group flex flex-col items-center cursor-pointer shrink-0 transition-transform duration-300 hover:scale-105 select-none';
      item.setAttribute('data-index', idx);
      item.setAttribute('role', 'button');
      item.setAttribute('tabindex', '0');
      item.setAttribute('aria-label', `View story: ${story.title}`);

      // Category Icon
      let icon = 'auto_awesome';
      if (story.category_code === 'festival') icon = 'celebration';
      else if (story.category_code === 'announcement') icon = 'campaign';
      else if (story.category_code === 'event') icon = 'event';

      item.innerHTML = `
        <div class="relative p-[2.5px] rounded-full bg-gradient-to-tr from-[#E8C176] via-[#FFDEB2] to-[#9A8F80] group-hover:from-[#FFE3A8] group-hover:to-[#E8C176] shadow-[0_0_15px_rgba(232,193,118,0.25)] group-hover:shadow-[0_0_22px_rgba(232,193,118,0.5)] transition-all duration-300 story-ring-active">
          <div class="p-[2.5px] bg-[#0E0E0E] rounded-full">
            <div class="w-16 h-16 sm:w-20 sm:h-20 rounded-full overflow-hidden bg-stone-900 flex items-center justify-center">
              <img src="${story.image_url}" alt="${escapeHtml(story.title)}"
                   class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                   loading="lazy" />
            </div>
          </div>
          <div class="absolute bottom-0 right-0 w-5 h-5 rounded-full bg-neutral-950 border border-[#E8C176] flex items-center justify-center text-[10px] text-[#E8C176] shadow">
            <span class="material-symbols-outlined text-[11px]">${icon}</span>
          </div>
        </div>
        <div class="mt-2 text-center max-w-[80px] sm:max-w-[90px]">
          <p class="text-[11px] sm:text-xs text-[#E5E2E1] font-medium truncate group-hover:text-[#E8C176] transition-colors font-body leading-tight">
            ${escapeHtml(story.title)}
          </p>
          <span class="text-[9px] uppercase tracking-wider text-[#9A8F80] font-label block truncate">
            ${escapeHtml(story.category)}
          </span>
        </div>
      `;

      item.addEventListener('click', () => openStory(idx));
      item.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          openStory(idx);
        }
      });

      listEl.appendChild(item);
    });
  }

  function setupEventListeners() {
    // Close button
    if (closeBtn) closeBtn.addEventListener('click', closeViewer);

    // Prev / Next buttons
    if (prevBtn) prevBtn.addEventListener('click', (e) => { e.stopPropagation(); prevStory(); });
    if (nextBtn) nextBtn.addEventListener('click', (e) => { e.stopPropagation(); nextStory(); });

    // Tap zones
    if (tapZoneLeft) tapZoneLeft.addEventListener('click', (e) => { e.stopPropagation(); prevStory(); });
    if (tapZoneRight) tapZoneRight.addEventListener('click', (e) => { e.stopPropagation(); nextStory(); });

    // Pause toggle
    if (pauseBtn) {
      pauseBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        togglePause();
      });
    }

    // Modal background click closes viewer
    if (viewerModal) {
      viewerModal.addEventListener('click', (e) => {
        if (e.target === viewerModal) closeViewer();
      });
    }

    // Keyboard navigation
    window.addEventListener('keydown', handleKeyDown);

    // Press-and-hold to pause story
    const cardEl = document.getElementById('storyCard');
    if (cardEl) {
      cardEl.addEventListener('mousedown', handlePointerDown);
      cardEl.addEventListener('mouseup', handlePointerUp);
      cardEl.addEventListener('mouseleave', handlePointerUp);

      // Touch events for hold-to-pause and swipe gestures
      cardEl.addEventListener('touchstart', handleTouchStart, { passive: true });
      cardEl.addEventListener('touchend', handleTouchEnd, { passive: true });
      cardEl.addEventListener('touchcancel', handlePointerUp, { passive: true });
    }
  }

  function handlePointerDown(e) {
    if (!isViewerOpen) return;
    if (e.target.closest('button')) return; // ignore clicks on buttons
    isPointerDown = true;
    pauseTimer();
  }

  function handlePointerUp() {
    if (!isViewerOpen || !isPointerDown) return;
    isPointerDown = false;
    if (!isPaused) {
      resumeTimer();
    }
  }

  function handleTouchStart(e) {
    if (!isViewerOpen || !e.touches || e.touches.length === 0) return;
    const touch = e.touches[0];
    touchStartX = touch.clientX;
    touchStartY = touch.clientY;
    touchStartTime = Date.now();
    isPointerDown = true;
    pauseTimer();
  }

  function handleTouchEnd(e) {
    if (!isViewerOpen) return;
    isPointerDown = false;
    const touchEndTime = Date.now();
    const duration = touchEndTime - touchStartTime;

    if (e.changedTouches && e.changedTouches.length > 0) {
      const touch = e.changedTouches[0];
      const deltaX = touch.clientX - touchStartX;
      const deltaY = touch.clientY - touchStartY;

      // Swipe Down to close
      if (deltaY > 90 && Math.abs(deltaX) < 80) {
        closeViewer();
        return;
      }

      // Swipe Left for Next
      if (deltaX < -60 && Math.abs(deltaY) < 60) {
        nextStory();
        return;
      }

      // Swipe Right for Prev
      if (deltaX > 60 && Math.abs(deltaY) < 60) {
        prevStory();
        return;
      }
    }

    // If hold was released without swipe, resume timer
    if (!isPaused) {
      resumeTimer();
    }
  }

  function handleKeyDown(e) {
    if (!isViewerOpen) return;

    if (e.key === 'Escape') {
      e.preventDefault();
      closeViewer();
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      nextStory();
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      prevStory();
    } else if (e.key === ' ') {
      e.preventDefault();
      togglePause();
    }
  }

  function openStory(index) {
    if (!stories || stories.length === 0) return;
    if (index < 0 || index >= stories.length) index = 0;

    currentIndex = index;
    isViewerOpen = true;
    isPaused = false;
    isPointerDown = false;

    viewerModal.classList.remove('hidden');
    viewerModal.classList.add('flex');
    document.body.style.overflow = 'hidden';

    renderProgressBars();
    loadStory(currentIndex);
  }

  function closeViewer() {
    isViewerOpen = false;
    stopTimer();
    if (viewerModal) {
      viewerModal.classList.add('hidden');
      viewerModal.classList.remove('flex');
    }
    document.body.style.overflow = '';
  }

  function renderProgressBars() {
    if (!progressBarContainer) return;
    progressBarContainer.innerHTML = '';

    stories.forEach((_, idx) => {
      const segment = document.createElement('div');
      segment.className = 'flex-1 h-1 bg-white/20 rounded-full overflow-hidden';
      
      const fill = document.createElement('div');
      fill.id = `storyProgressFill_${idx}`;
      fill.className = 'progress-fill h-full bg-[#E8C176]';
      
      if (idx < currentIndex) {
        fill.style.width = '100%';
      } else {
        fill.style.width = '0%';
      }

      segment.appendChild(fill);
      progressBarContainer.appendChild(segment);
    });
  }

  function loadStory(index) {
    if (index < 0 || index >= stories.length) {
      closeViewer();
      return;
    }

    stopTimer();
    isImageLoaded = false;
    progressElapsedBeforePause = 0;

    const story = stories[index];

    // Update Header Text
    if (viewerTitle) viewerTitle.textContent = story.title || '';
    if (viewerCategory) viewerCategory.textContent = story.category || 'General';
    if (viewerTimeAgo) viewerTimeAgo.textContent = formatTimeAgo(story.published_at);

    // Update Description
    if (viewerDescription && viewerCaptionBox) {
      if (story.description && story.description.trim()) {
        viewerDescription.textContent = story.description.trim();
        viewerCaptionBox.classList.remove('hidden');
      } else {
        viewerDescription.textContent = '';
        viewerCaptionBox.classList.add('hidden');
      }
    }

    // Reset progress bar widths
    stories.forEach((_, i) => {
      const fill = document.getElementById(`storyProgressFill_${i}`);
      if (fill) {
        if (i < currentIndex) {
          fill.style.width = '100%';
        } else {
          fill.style.width = '0%';
        }
      }
    });

    // Show loading spinner
    if (viewerLoader) viewerLoader.classList.remove('hidden');
    if (viewerImage) {
      viewerImage.classList.add('opacity-0');
      viewerImage.classList.remove('opacity-100');
    }

    // Preload image
    const img = new Image();
    img.src = story.image_url;

    img.onload = () => {
      if (!isViewerOpen || currentIndex !== index) return;
      if (viewerImage) {
        viewerImage.src = story.image_url;
        viewerImage.classList.remove('opacity-0');
        viewerImage.classList.add('opacity-100');
      }
      if (viewerAmbientBg) {
        viewerAmbientBg.src = story.image_url;
      }
      if (viewerLoader) viewerLoader.classList.add('hidden');
      isImageLoaded = true;

      // Start 5s countdown
      startTimer();
    };

    img.onerror = () => {
      if (viewerLoader) viewerLoader.classList.add('hidden');
      console.error('Failed to load story poster:', story.image_url);
      // Automatically advance to next after brief delay
      setTimeout(() => nextStory(), 1500);
    };
  }

  function startTimer() {
    stopTimer();
    if (!isImageLoaded) return;
    progressStartTime = performance.now() - progressElapsedBeforePause;
    runProgressLoop();
  }

  function runProgressLoop() {
    animFrameId = requestAnimationFrame((now) => {
      if (!isViewerOpen || isPaused) return;

      const elapsed = now - progressStartTime;
      const pct = Math.min(100, (elapsed / storyDuration) * 100);

      const fill = document.getElementById(`storyProgressFill_${currentIndex}`);
      if (fill) {
        fill.style.width = `${pct}%`;
      }

      if (elapsed >= storyDuration) {
        // Story finished! Advance to next
        nextStory();
      } else {
        runProgressLoop();
      }
    });
  }

  function pauseTimer() {
    if (!animFrameId) return;
    cancelAnimationFrame(animFrameId);
    animFrameId = null;
    progressElapsedBeforePause = performance.now() - progressStartTime;
  }

  function resumeTimer() {
    if (!isImageLoaded || animFrameId) return;
    progressStartTime = performance.now() - progressElapsedBeforePause;
    runProgressLoop();
  }

  function stopTimer() {
    if (animFrameId) {
      cancelAnimationFrame(animFrameId);
      animFrameId = null;
    }
  }

  function togglePause() {
    if (isPaused) {
      isPaused = false;
      if (pauseIcon) pauseIcon.textContent = 'pause';
      resumeTimer();
    } else {
      isPaused = true;
      if (pauseIcon) pauseIcon.textContent = 'play_arrow';
      pauseTimer();
    }
  }

  function nextStory() {
    if (currentIndex < stories.length - 1) {
      currentIndex++;
      loadStory(currentIndex);
    } else {
      // Completed the last story
      closeViewer();
    }
  }

  function prevStory() {
    if (currentIndex > 0) {
      currentIndex--;
      loadStory(currentIndex);
    } else {
      // Restart first story
      loadStory(0);
    }
  }

  function formatTimeAgo(isoDate) {
    if (!isoDate) return '';
    try {
      const diffMs = Date.now() - new Date(isoDate).getTime();
      const diffSec = Math.floor(diffMs / 1000);
      if (diffSec < 60) return 'Just now';
      const diffMin = Math.floor(diffSec / 60);
      if (diffMin < 60) return `${diffMin}m ago`;
      const diffHours = Math.floor(diffMin / 60);
      if (diffHours < 24) return `${diffHours}h ago`;
      const diffDays = Math.floor(diffHours / 24);
      return `${diffDays}d ago`;
    } catch (e) {
      return '';
    }
  }

  function escapeHtml(text) {
    if (!text) return '';
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;',
    };
    return String(text).replace(/[&<>"']/g, (m) => map[m]);
  }

  // Initialize once DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Expose on window for programmatic control or testing
  window.MomentorsoStories = {
    openStory,
    closeViewer,
    nextStory,
    prevStory,
    togglePause,
    fetchStories,
    getStories: () => stories,
  };
})();
