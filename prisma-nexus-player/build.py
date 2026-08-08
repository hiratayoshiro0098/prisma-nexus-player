import os
import sys
import shutil
import subprocess

def build_executable():
    """Build standalone executable with PyInstaller"""
    
    print("=" * 60)
    print("🔨 Building PrismaNexus Player Executable")
    print("=" * 60)
    
    # Clean old builds
    for folder in ['dist', 'build']:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"✅ Cleaned {folder}/")
    
    # Ensure static folder exists
    os.makedirs('static', exist_ok=True)
    
    # PyInstaller command
    cmd = [
        'pyinstaller',
        '--name=PrismaNexusPlayer',
        '--onefile',
        '--windowed',
        '--add-data=static;static',
        '--hidden-import=flask',
        '--hidden-import=flask_cors',
        '--noconsole',
        'app.py'
    ]
    
    print("\n📦 Running PyInstaller...")
    print(f"Command: {' '.join(cmd)}\n")
    
    try:
        subprocess.run(cmd, check=True)
        print("\n" + "=" * 60)
        print("✅ Build successful!")
        print(f"📁 Executable: dist/PrismaNexusPlayer.exe")
        print("=" * 60)
        
        # Create release folder
        release_dir = 'release'
        if os.path.exists(release_dir):
            shutil.rmtree(release_dir)
        os.makedirs(release_dir)
        
        # Copy executable
        shutil.copy('dist/PrismaNexusPlayer.exe', release_dir)
        
        # Create README for release
        with open(os.path.join(release_dir, 'README.txt'), 'w') as f:
            f.write("""
PrismaNexus Player (PNP) v2.0
==============================

Thank you for downloading PrismaNexus Player!

To run:
1. Double-click PrismaNexusPlayer.exe
2. Your browser will open automatically
3. Click "Scan Music" or "Scan Videos" to load media
4. Enjoy!

Requirements:
- Windows 7 or higher
- Modern web browser (Chrome, Edge, Firefox)
- No installation needed!

For more information, visit:
https://github.com/YOUR_USERNAME/prisma-nexus-player

Enjoy! 🔮
            """.strip())
        
        print(f"✅ Release folder created: {release_dir}/")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("\n❌ PyInstaller not found. Install it with: pip install pyinstaller")
        sys.exit(1)

if __name__ == '__main__':
    build_executable()