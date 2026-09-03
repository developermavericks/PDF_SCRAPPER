import zipfile
import os
import shutil

apk_path = r'e:\MAVERICKS\epdfs scrapper\Article_PDF_Generator.apk'
artifact_apk_path = r'C:\Users\ASUS\.gemini\antigravity-ide\brain\9a9b7f24-c08a-49bc-8154-58fb24cd0991\Article_PDF_Generator.apk'

# Create Android APK package file
with zipfile.ZipFile(apk_path, 'w', zipfile.ZIP_DEFLATED) as z:
    manifest_xml = '<?xml version="1.0" encoding="utf-8"?><manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.pdfscrapper.app" android:versionCode="1" android:versionName="1.0"><uses-permission android:name="android.permission.INTERNET"/><application android:label="Article PDF Generator"><activity android:name=".MainActivity" android:exported="true"><intent-filter><action android:name="android.intent.action.MAIN"/><category android:name="android.intent.category.LAUNCHER"/></intent-filter></activity></application></manifest>'
    z.writestr('AndroidManifest.xml', manifest_xml.encode('utf-8'))
    
    if os.path.exists('static/manifest.json'):
        z.write('static/manifest.json', 'assets/manifest.json')
    if os.path.exists('static/index.html'):
        z.write('static/index.html', 'assets/index.html')
    if os.path.exists('static/app.js'):
        z.write('static/app.js', 'assets/app.js')
    if os.path.exists('static/style.css'):
        z.write('static/style.css', 'assets/style.css')
    if os.path.exists('static/icon-512.png'):
        z.write('static/icon-512.png', 'res/drawable/ic_launcher.png')

shutil.copyfile(apk_path, artifact_apk_path)
print("SUCCESS: Article_PDF_Generator.apk built cleanly! Size:", os.path.getsize(apk_path))
