from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
from datetime import datetime
import os

class SimpleVideoTester:
    def __init__(self, video_url):
        self.html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Video Tester</title>
            <style>
                .container {{ margin: 20px; }}
                video {{ max-width: 800px; }}
                #status {{ margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div id="status">Loading video...</div>
                <video controls>
                    <source src="{video_url}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
            </div>
            <script>
                const video = document.querySelector('video');
                const status = document.querySelector('#status');
                
                video.addEventListener('loadedmetadata', () => {{
                    status.textContent = 'Video metadata loaded';
                }});
                
                video.addEventListener('canplay', () => {{
                    status.textContent = 'Video ready to play';
                    window.videoReady = true;
                }});
                
                video.addEventListener('error', () => {{
                    status.textContent = 'Error loading video: ' + (video.error ? video.error.message : 'unknown error');
                }});
            </script>
        </body>
        </html>
        """
        
    def create_test_page(self):
        with open('test_video.html', 'w') as f:
            f.write(self.html_template)
            
    def wait_for_video_ready(self, driver, timeout=10):
        """Wait for video to be ready to play"""
        print("Waiting for video to load...")
        try:
            # Wait for video element
            video = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "video"))
            )
            
            # Wait for video to be ready
            start_time = time.time()
            while time.time() - start_time < timeout:
                status = driver.execute_script("""
                    const video = document.querySelector('video');
                    const status = document.querySelector('#status');
                    return {
                        ready: window.videoReady,
                        status: status.textContent,
                        readyState: video.readyState,
                        error: video.error ? video.error.message : null
                    }
                """)
                
                print(f"Video status: {status['status']}")
                
                if status['error']:
                    raise Exception(f"Video loading error: {status['error']}")
                
                if status['ready'] and status['readyState'] >= 3:
                    return True
                    
                time.sleep(1)
                
            raise Exception("Timeout waiting for video to be ready")
            
        except Exception as e:
            print(f"Error waiting for video: {str(e)}")
            return False
            
    def run_test(self):
        self.create_test_page()
        driver = webdriver.Chrome()
        
        try:
            # Open the test page
            driver.get(f"file://{os.path.abspath('test_video.html')}")
            print("Opened test page successfully")
            
            results = {
                "timestamp": datetime.now().isoformat(),
                "tests": []
            }
            
            # Wait for video to be ready
            video_ready = self.wait_for_video_ready(driver)
            results["tests"].append({
                "name": "Video Loading",
                "status": "PASS" if video_ready else "FAIL"
            })
            
            if video_ready:
                # Test video properties
                try:
                    video_props = driver.execute_script("""
                        const video = document.querySelector('video');
                        return {
                            duration: video.duration,
                            width: video.videoWidth,
                            height: video.videoHeight,
                            readyState: video.readyState,
                            networkState: video.networkState,
                            error: video.error ? video.error.message : null
                        }
                    """)
                    results["tests"].append({
                        "name": "Video Properties",
                        "details": video_props
                    })
                    print("Video properties:", video_props)
                except Exception as e:
                    results["tests"].append({
                        "name": "Video Properties",
                        "status": "FAIL",
                        "error": str(e)
                    })
                
                # Test playback
                try:
                    driver.execute_script("document.querySelector('video').play()")
                    time.sleep(2)
                    playback_state = driver.execute_script("""
                        const video = document.querySelector('video');
                        return {
                            playing: !video.paused,
                            currentTime: video.currentTime,
                            error: video.error ? video.error.message : null
                        }
                    """)
                    results["tests"].append({
                        "name": "Video Playback",
                        "status": "PASS" if playback_state['playing'] else "FAIL",
                        "details": playback_state
                    })
                    print("Playback state:", playback_state)
                except Exception as e:
                    results["tests"].append({
                        "name": "Video Playback",
                        "status": "FAIL",
                        "error": str(e)
                    })
            
            # Save results
            with open('video_test_results.json', 'w') as f:
                json.dump(results, f, indent=2)
            
            return results
            
        finally:
            driver.quit()

def test_video(video_url):
    print(f"\nTesting video: {video_url}")
    tester = SimpleVideoTester(video_url)
    results = tester.run_test()
    
    print("\nTest Results:")
    print("-" * 50)
    for test in results["tests"]:
        print(f"{test['name']}: {test.get('status', 'See details')}")
        if 'details' in test:
            print("Details:", test['details'])
        if 'error' in test:
            print("Error:", test['error'])
    
    print("\nFull results saved to video_test_results.json")

if __name__ == "__main__":
    TEST_VIDEOS = {
        "Big Buck Bunny (small)": "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/Big_Buck_Bunny_360_10s_1MB.mp4",
        "Tears of Steel (small)": "https://test-videos.co.uk/vids/tearsofsteel/mp4/360/tears_of_steel_360p_10s.mp4"
    }
    
    print("Available test videos:")
    for i, (name, url) in enumerate(TEST_VIDEOS.items(), 1):
        print(f"{i}. {name}")
    
    choice = input("\nEnter the number of the video you want to test (or paste a URL): ")
    
    if choice.isdigit() and 1 <= int(choice) <= len(TEST_VIDEOS):
        video_url = list(TEST_VIDEOS.values())[int(choice) - 1]
    else:
        video_url = choice
    
    test_video(video_url)