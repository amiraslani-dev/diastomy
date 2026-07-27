document.addEventListener("alpine:init", () => {
                Alpine.data("customPlayer", () => ({
                    isPlaying: false,
                    isMuted: false,
                    isFullscreen: false,
                    isDragging: false,
                    isLocked: false,
                    showControls: true,
                    showPreview: false,
                    previewPos: 0,
                    previewTimeFormatted: "۰:۰۰",
                    controlsTimeout: null,
                    progress: 0,
                    currentTimeFormatted: "۰:۰۰",
                    durationFormatted: "۰:۰۰",
                    clickTimeout: null,

                    // متغیرهای مدیریت منوها
                    showSpeedMenu: false,
                    showQualityMenu: false,
                    showCcMenu: false,
                    showEpisodesMenu: false, // متغیر جدید

                    // دیتای قسمت‌ها (لیست نمایشی طولانی برای فعال‌شدن اسکرول)
                    currentEpisode: 1,
                    episodes: Array.from({ length: 8 }, (_, i) => i + 1),

                    // دیتای سرعت و کیفیت
                    playbackRate: 1,
                    playbackRates: [0.25, 0.5, 1, 1.5, 2],
                    currentQuality: "Auto",
                    qualityOptions: [
                        "Auto",
                        "360p (290kbps)",
                        "480p (440kbps)",
                        "720p (930kbps)",
                        "1080p (1530kbps)",
                    ],

                    // دیتای شخصی‌سازی زیرنویس
                    ccLang: "فارسی",
                    ccLangs: ["فارسی", "English", "خاموش"],
                    ccSize: "متوسط",
                    ccSizes: ["کوچک", "متوسط", "بزرگ", "خیلی بزرگ"],
                    ccColor: "سفید",
                    ccColors: ["سفید", "زرد", "بنفش", "نیلی"],
                    ccBg: "بی رنگ",
                    ccBgs: ["بی رنگ", "مشکی کم رنگ", "مشکی"],

                    init() {
                        this.$nextTick(() => {
                            const video = this.$refs.videoPlayer;
                            if (video.readyState >= 1) {
                                this.initVideo();
                            }
                            this.setCcLang(this.ccLang);
                            this.applyCcStyles();
                        });
                        document.addEventListener("fullscreenchange", () => {
                            this.isFullscreen = !!document.fullscreenElement;
                        });
                        this.resetControlsTimeout();
                    },

                    // باز و بسته شدن هوشمند منوها
                    openMenu(type) {
                        this.closeMenus();
                        if (type === "speed") this.showSpeedMenu = true;
                        if (type === "quality") this.showQualityMenu = true;
                        if (type === "cc") this.showCcMenu = true;
                        if (type === "episodes") this.showEpisodesMenu = true;
                    },
                    closeMenus() {
                        this.showSpeedMenu = false;
                        this.showQualityMenu = false;
                        this.showCcMenu = false;
                        this.showEpisodesMenu = false;
                    },

                    setSpeed(rate) {
                        this.playbackRate = rate;
                        this.$refs.videoPlayer.playbackRate = rate;
                        this.closeMenus();
                        this.resetControlsTimeout();
                    },

                    setQuality(quality) {
                        this.currentQuality = quality;
                        this.closeMenus();
                        this.resetControlsTimeout();
                    },

                    setCcLang(lang) {
                        this.ccLang = lang;
                        const video = this.$refs.videoPlayer;
                        for (let i = 0; i < video.textTracks.length; i++) {
                            const track = video.textTracks[i];
                            if (lang === "خاموش") {
                                track.mode = "disabled";
                            } else if (
                                track.label === lang ||
                                track.language === lang
                            ) {
                                track.mode = "showing";
                            } else {
                                track.mode = "disabled";
                            }
                        }
                    },
                    setCcStyle(type, value) {
                        if (type === "size") this.ccSize = value;
                        if (type === "color") this.ccColor = value;
                        if (type === "bg") this.ccBg = value;
                        this.applyCcStyles();
                    },
                    applyCcStyles() {
                        const sizes = {
                            کوچک: "75%",
                            متوسط: "100%",
                            بزرگ: "150%",
                            "خیلی بزرگ": "200%",
                        };
                        const colors = {
                            سفید: "#ffffff",
                            زرد: "#ffff00",
                            بنفش: "#800080",
                            نیلی: "#00ffff",
                        };
                        const bgs = {
                            "بی رنگ": "transparent",
                            "مشکی کم رنگ": "rgba(0,0,0,0.5)",
                            مشکی: "rgba(0,0,0,1)",
                        };

                        const css = `
                    video::cue {
                        font-size: ${sizes[this.ccSize]} !important;
                        color: ${colors[this.ccColor]} !important;
                        background-color: ${bgs[this.ccBg]} !important;
                        font-family: inherit !important;
                        text-shadow: 1px 1px 2px black !important;
                    }
                `;

                        let styleTag =
                            document.getElementById("custom-cc-styles");
                        if (!styleTag) {
                            styleTag = document.createElement("style");
                            styleTag.id = "custom-cc-styles";
                            document.head.appendChild(styleTag);
                        }
                        styleTag.innerHTML = css;
                    },

                    updatePreview(e) {
                        const bar = this.$refs.progressBar;
                        const mainVideo = this.$refs.videoPlayer;
                        const prevVideo = this.$refs.previewVideo;

                        if (!mainVideo.duration || !bar) return;

                        const rect = bar.getBoundingClientRect();
                        const clientX = e.touches
                            ? e.touches[0].clientX
                            : e.clientX;

                        let pos = (clientX - rect.left) / rect.width;
                        pos = Math.max(0, Math.min(1, pos));

                        this.previewPos = pos * 100;

                        const hoverTime = pos * mainVideo.duration;
                        this.previewTimeFormatted = this.formatTime(hoverTime);

                        if (prevVideo) {
                            prevVideo.currentTime = hoverTime;
                        }
                    },

                    toggleLock() {
                        this.isLocked = !this.isLocked;
                        this.resetControlsTimeout();
                    },

                    resetControlsTimeout() {
                        this.showControls = true;
                        clearTimeout(this.controlsTimeout);
                        if (
                            ((this.isPlaying && !this.isDragging) ||
                                this.isLocked) &&
                            !this.showSpeedMenu &&
                            !this.showQualityMenu &&
                            !this.showCcMenu &&
                            !this.showEpisodesMenu
                        ) {
                            this.controlsTimeout = setTimeout(() => {
                                this.showControls = false;
                            }, 2000);
                        }
                    },

                    hideControls() {
                        if (
                            ((this.isPlaying && !this.isDragging) ||
                                this.isLocked) &&
                            !this.showSpeedMenu &&
                            !this.showQualityMenu &&
                            !this.showCcMenu &&
                            !this.showEpisodesMenu
                        ) {
                            this.showControls = false;
                            clearTimeout(this.controlsTimeout);
                        }
                    },

                    handleVideoClick() {
                        if (
                            this.showSpeedMenu ||
                            this.showQualityMenu ||
                            this.showCcMenu ||
                            this.showEpisodesMenu
                        ) {
                            this.closeMenus();
                            this.resetControlsTimeout();
                            return;
                        }

                        if (!this.showControls || this.isLocked) {
                            this.resetControlsTimeout();
                            return;
                        }

                        this.resetControlsTimeout();
                        if (this.clickTimeout) {
                            clearTimeout(this.clickTimeout);
                            this.clickTimeout = null;
                            this.toggleFullscreen();
                        } else {
                            this.clickTimeout = setTimeout(() => {
                                this.togglePlay();
                                this.clickTimeout = null;
                            }, 250);
                        }
                    },

                    toggleFullscreen() {
                        const container = this.$refs.playerContainer;
                        if (
                            !document.fullscreenElement &&
                            !document.webkitFullscreenElement
                        ) {
                            const requestFS =
                                container.requestFullscreen ||
                                container.webkitRequestFullscreen ||
                                container.msRequestFullscreen;
                            if (requestFS) {
                                const promise = requestFS.call(container);
                                if (promise) {
                                    promise
                                        .then(() => this.lockLandscape())
                                        .catch((e) => {});
                                } else {
                                    this.lockLandscape();
                                }
                            }
                        } else {
                            const exitFS =
                                document.exitFullscreen ||
                                document.webkitExitFullscreen ||
                                document.msExitFullscreen;
                            if (exitFS) {
                                const promise = exitFS.call(document);
                                if (promise) {
                                    promise
                                        .then(() => this.unlockLandscape())
                                        .catch((e) => {});
                                } else {
                                    this.unlockLandscape();
                                }
                            }
                        }
                    },

                    lockLandscape() {
                        if (screen.orientation && screen.orientation.lock) {
                            screen.orientation
                                .lock("landscape")
                                .catch(() => {});
                        }
                    },

                    unlockLandscape() {
                        if (screen.orientation && screen.orientation.unlock) {
                            screen.orientation.unlock();
                        }
                    },

                    togglePlay() {
                        const video = this.$refs.videoPlayer;
                        if (video.paused) {
                            video.play();
                            this.isPlaying = true;
                            this.resetControlsTimeout();
                        } else {
                            video.pause();
                            this.isPlaying = false;
                            this.showControls = true;
                            clearTimeout(this.controlsTimeout);
                        }
                    },

                    toggleMute() {
                        this.isMuted = !this.isMuted;
                        this.$refs.videoPlayer.muted = this.isMuted;
                    },

                    skip(seconds) {
                        const video = this.$refs.videoPlayer;
                        video.currentTime += seconds;
                        this.resetControlsTimeout();
                    },

                    initVideo() {
                        const video = this.$refs.videoPlayer;
                        if (video.duration) {
                            this.durationFormatted = this.formatTime(
                                video.duration,
                            );
                        }
                        video.playbackRate = this.playbackRate;
                    },

                    updateProgress() {
                        if (this.isDragging) return;
                        const video = this.$refs.videoPlayer;
                        if (!video.duration) return;

                        if (
                            this.durationFormatted === "۰:۰۰" ||
                            this.durationFormatted === "NaN:NaN"
                        ) {
                            this.durationFormatted = this.formatTime(
                                video.duration,
                            );
                        }

                        this.progress =
                            (video.currentTime / video.duration) * 100;
                        this.currentTimeFormatted = this.formatTime(
                            video.currentTime,
                        );
                    },

                    startDrag(e) {
                        if (this.isLocked) return;
                        this.isDragging = true;
                        this.showControls = true;
                        clearTimeout(this.controlsTimeout);
                        this.updateSeek(e);

                        const moveHandler = (e) => this.updateSeek(e);
                        const stopHandler = () => {
                            this.isDragging = false;
                            this.resetControlsTimeout();
                            window.removeEventListener(
                                "mousemove",
                                moveHandler,
                            );
                            window.removeEventListener("mouseup", stopHandler);
                            window.removeEventListener(
                                "touchmove",
                                moveHandler,
                            );
                            window.removeEventListener("touchend", stopHandler);
                        };

                        window.addEventListener("mousemove", moveHandler);
                        window.addEventListener("mouseup", stopHandler);
                        window.addEventListener("touchmove", moveHandler);
                        window.addEventListener("touchmove", moveHandler);
                        window.addEventListener("touchend", stopHandler);
                    },

                    updateSeek(e) {
                        const video = this.$refs.videoPlayer;
                        const bar = this.$refs.progressBar;
                        if (!video.duration || !bar) return;

                        const rect = bar.getBoundingClientRect();
                        const clientX = e.touches
                            ? e.touches[0].clientX
                            : e.clientX;

                        let pos = (clientX - rect.left) / rect.width;
                        pos = Math.max(0, Math.min(1, pos));

                        this.progress = pos * 100;
                        video.currentTime = pos * video.duration;
                        this.currentTimeFormatted = this.formatTime(
                            video.currentTime,
                        );
                    },

                    formatTime(timeInSeconds) {
                        if (isNaN(timeInSeconds)) return "۰:۰۰";
                        const h = Math.floor(timeInSeconds / 3600);
                        const m = Math.floor((timeInSeconds % 3600) / 60);
                        const s = Math.floor(timeInSeconds % 60);

                        let formatted =
                            h > 0
                                ? `${h}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`
                                : `${m}:${s.toString().padStart(2, "0")}`;

                        const persianDigits = [
                            "۰",
                            "۱",
                            "۲",
                            "۳",
                            "۴",
                            "۵",
                            "۶",
                            "۷",
                            "۸",
                            "۹",
                        ];
                        return formatted.replace(
                            /\d/g,
                            (x) => persianDigits[x],
                        );
                    },
                }));
            });
