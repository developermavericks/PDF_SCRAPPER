import os
import subprocess
import shutil
import zipfile

java_home = r'C:\Program Files\Android\Android Studio\jbr'
android_sdk = r'C:\Users\ASUS\AppData\Local\Android\Sdk'
build_tools = os.path.join(android_sdk, 'build-tools', '36.0.0')
android_jar = os.path.join(android_sdk, 'platforms', 'android-36', 'android.jar')

env = os.environ.copy()
env['JAVA_HOME'] = java_home
env['ANDROID_HOME'] = android_sdk
env['PATH'] = os.path.join(java_home, 'bin') + ';' + build_tools + ';' + env['PATH']

javac = os.path.join(java_home, 'bin', 'javac.exe')
keytool = os.path.join(java_home, 'bin', 'keytool.exe')

aapt2 = os.path.join(build_tools, 'aapt2.exe')
d8 = os.path.join(build_tools, 'd8.bat')
apksigner = os.path.join(build_tools, 'apksigner.bat')
zipalign = os.path.join(build_tools, 'zipalign.exe')

work_dir = os.path.abspath('apk_build_temp')
if os.path.exists(work_dir):
    shutil.rmtree(work_dir)
os.makedirs(work_dir, exist_ok=True)

# 1. Compile Java Source Code to Class Files
print('[1/5] Compiling Java source code with javac...')
classes_dir = os.path.join(work_dir, 'classes')
os.makedirs(classes_dir, exist_ok=True)

java_src = os.path.abspath(r'android_app\MainActivity.java')
cmd_javac = [
    javac,
    '-source', '1.8',
    '-target', '1.8',
    '-cp', android_jar,
    '-d', classes_dir,
    java_src
]
res = subprocess.run(cmd_javac, capture_output=True, text=True, env=env)
if res.returncode != 0:
    print('Javac Error:', res.stderr)
    exit(1)
print('Java compilation successful!')

# 2. Convert Class Files to Dalvik Executable (classes.dex) using D8
print('[2/5] Converting bytecode to classes.dex using D8...')
dex_dir = os.path.join(work_dir, 'dex')
os.makedirs(dex_dir, exist_ok=True)

class_file = os.path.join(classes_dir, 'com', 'pdfscrapper', 'app', 'MainActivity.class')
class_inner = os.path.join(classes_dir, 'com', 'pdfscrapper', 'app', 'MainActivity$1.class')

class_files = [class_file]
if os.path.exists(class_inner):
    class_files.append(class_inner)

cmd_d8 = [d8, '--lib', android_jar, '--output', dex_dir] + class_files
res = subprocess.run(cmd_d8, capture_output=True, text=True, shell=True, env=env)
if res.returncode != 0:
    print('D8 Error:', res.stderr, res.stdout)
    exit(1)
print('D8 DEX conversion successful!')

# 3. Compile and Link Resources using AAPT2 (Android 14/15 Modern Format)
print('[3/5] Compiling & linking resources with AAPT2...')
manifest = os.path.abspath(r'android_app\AndroidManifest.xml')
res_dir = os.path.join(work_dir, 'res')
os.makedirs(os.path.join(res_dir, 'mipmap'), exist_ok=True)

if os.path.exists(r'static\icon-192.png'):
    shutil.copyfile(r'static\icon-192.png', os.path.join(res_dir, 'mipmap', 'ic_launcher.png'))

compiled_res = os.path.join(work_dir, 'compiled_res.zip')
cmd_aapt2_compile = [
    aapt2, 'compile',
    '--dir', res_dir,
    '-o', compiled_res
]
res = subprocess.run(cmd_aapt2_compile, capture_output=True, text=True, env=env)
if res.returncode != 0:
    print('AAPT2 Compile Error:', res.stderr)
    exit(1)

unsigned_apk = os.path.join(work_dir, 'unsigned.apk')
cmd_aapt2_link = [
    aapt2, 'link',
    '-o', unsigned_apk,
    '-I', android_jar,
    '--manifest', manifest,
    '--auto-add-overlay',
    compiled_res
]
res = subprocess.run(cmd_aapt2_link, capture_output=True, text=True, env=env)
if res.returncode != 0:
    print('AAPT2 Link Error:', res.stderr)
    exit(1)
print('AAPT2 compilation & linking successful!')

# Add classes.dex to unsigned APK
dex_file = os.path.join(dex_dir, 'classes.dex')
with zipfile.ZipFile(unsigned_apk, 'a') as z:
    z.write(dex_file, 'classes.dex')

# 4. Align APK using Zipalign
print('[4/5] Aligning APK with zipalign...')
aligned_apk = os.path.join(work_dir, 'aligned.apk')
cmd_zipalign = [zipalign, '-f', '-p', '4', unsigned_apk, aligned_apk]
res = subprocess.run(cmd_zipalign, capture_output=True, text=True, env=env)
if res.returncode != 0:
    print('Zipalign Error:', res.stderr)
    exit(1)

# 5. Sign APK with Android Keystore using Keytool & Apksigner
print('[5/5] Signing APK with keystore...')
keystore = os.path.join(work_dir, 'debug.keystore')
if not os.path.exists(keystore):
    cmd_keytool = [
        keytool, '-genkey', '-v',
        '-keystore', keystore,
        '-alias', 'androiddebugkey',
        '-keyalg', 'RSA',
        '-keysize', '2048',
        '-validity', '10000',
        '-storepass', 'android',
        '-keypass', 'android',
        '-dname', 'CN=Android Debug,O=Android,C=US'
    ]
    subprocess.run(cmd_keytool, capture_output=True, text=True, env=env)

final_apk = os.path.abspath(r'e:\MAVERICKS\epdfs scrapper\Article_PDF_Generator_Native.apk')

cmd_sign = [
    apksigner, 'sign',
    '--ks', keystore,
    '--ks-pass', 'pass:android',
    '--key-pass', 'pass:android',
    '--out', final_apk,
    aligned_apk
]
res = subprocess.run(cmd_sign, capture_output=True, text=True, shell=True, env=env)
if res.returncode != 0:
    print('Apksigner Error:', res.stderr, res.stdout)
    exit(1)

artifact_apk = r'C:\Users\ASUS\.gemini\antigravity-ide\brain\9a9b7f24-c08a-49bc-8154-58fb24cd0991\Article_PDF_Generator_Native.apk'
shutil.copyfile(final_apk, artifact_apk)

print('========================================================')
print('SUCCESS! AAPT2 Android 14/15 Compliant APK generated!')
print('File:', final_apk)
print('Size:', os.path.getsize(final_apk), 'bytes')
print('========================================================')
