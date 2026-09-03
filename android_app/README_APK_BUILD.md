# 📱 Android APK Installation & Build Guide

There are **2 easy ways** to get the app onto your Android phone:

---

## Method 1: Instant WebAPK Installation (No Android Studio Required) ⭐

1. Run [`start_mobile_server.bat`](file:///e:/MAVERICKS/epdfs%20scrapper/start_mobile_server.bat) on your PC.
2. Open Chrome on your Android phone and navigate to your server's Wi-Fi IP (e.g., `http://192.168.1.5:8000`).
3. Tap **📲 Install App** in the app header (or open Chrome menu `⋮` ➔ **Add to Home screen**).
4. Android will build and install a native **WebAPK app** directly onto your home screen!

### 🎯 Native Android Share Support:
Once installed, whenever you are reading an article on Chrome, Twitter, LinkedIn, or Reddit on Android:
1. Tap **Share** ➔ Select **Article PDF Generator**.
2. The app opens automatically, pre-fills the article URL, and generates your downloadable PDF!

---

## Method 2: Build Standalone APK via PWABuilder CLI or Android Studio

### Using PWABuilder (Recommended for instant APK file):
1. Run `npx @pwabuilder/cli http://localhost:8000 -v android`
2. It outputs an installable `.apk` file directly in 10 seconds!

### Using Android Studio:
1. Open Android Studio.
2. Select **Open an existing project** and choose the [`android_app`](file:///e:/MAVERICKS/epdfs%20scrapper/android_app/) folder.
3. Click **Build ➔ Build APK(s)** to generate `app-debug.apk`.
4. Copy the `.apk` file to your phone and tap to install!
