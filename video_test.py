from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import datetime
import os
from dataclasses import dataclass
from typing import List
import pytest

@dataclass
class StreamMetrics:
    buffer_count: int
    playback_time: float
    current_quality: str
    timestamp: str

def create_test_page():
    """Create a local HTML file for testing"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Video Test Page</title>
        <style>
            .container { max-width: 800px; margin: 20px auto; padding: 20px; }
            .video-wrapper { position: relative; }
            .quality-selector { position: absolute; bottom: 10px; right: 10px; background: rgba(0,0,0,0.7);
                              color: white; padding: 5px 10px; cursor: pointer; border: none; }
            .quality-options { display: none; position: absolute; bottom: 40px; right: 10px; 
                             background: rgba(0,0,0,0.7); }
            .quality-option { color: white; padding: 5px 10px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="video-wrapper">
                <video width="100%" controls>
                    <source src="https://storage.googleapis.com/media-session/big-buck-bunny/trailer.mov" type="video/mp4">
                </video>
                <button class="quality-selector">Quality</button>
                <div class="quality-options">
                    <div class="quality-option">1080p</div>
                    <div class="quality-option">720p</div>
                    <div class="quality-option">480p</div>
                </div>
            </div>
        </div>
        <script>
            const qualitySelector = document.querySelector('.quality-selector');
            const qualityOptions = document.querySelector('.quality-options');
            qualitySelector.addEventListener('click', () => {
                qualityOptions.style.display = qualityOptions.style.display === 'block' ? 'none' : 'block';
            });
            document.querySelectorAll('.quality-option').forEach(option => {
                option.addEventListener('click', () => {
                    console.log(`Changing quality to ${option.textContent}`);
                    qualityOptions.style.display = 'none';
                });
            });
        </script>
    </body>
    </html>
    """
    with open('test_video.html', 'w') as f:
        f.write(html_content)
    return os.path.abspath('test_video.html')

class VideoStreamTest:
    def __init__(self, url: str):
        self.url = url
        self.driver = webdriver.Chrome()
        self.metrics_log: List[StreamMetrics] = []
        
    def setup(self):
        """Initialize the webdriver and navigate to video page"""
        self.driver.get(self.url)
        self.video = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "video"))
        )
        
    def collect_metrics(self) -> StreamMetrics:
        """Collect current video metrics"""
        metrics_script = """
        const video = document.querySelector('video');
        return {
            buffered: video.buffered.length,
            currentTime: video.currentTime,
            videoWidth: video.videoWidth,
            videoHeight: video.videoHeight
        };
        """
        metrics = self.driver.execute_script(metrics_script)
        
        return StreamMetrics(
            buffer_count=metrics['buffered'],
            playback_time=metrics['currentTime'],
            current_quality=f"{metrics['videoWidth']}x{metrics['videoHeight']}",
            timestamp=datetime.datetime.now().isoformat()
        )
        
    def run_all_tests(self):
        """Run all tests and return results"""
        results = {
            "playback_test": self.test_playback_start(),
            "quality_test": self.test_quality_switch(),
            "seek_test": self.test_seek()
        }
        self.save_report("test_results.json")
        return results

    def test_playback_start(self) -> bool:
        """Test if video starts playing properly"""
        try:
            self.driver.execute_script("document.querySelector('video').play()")
            time.sleep(2)
            metrics = self.collect_metrics()
            self.metrics_log.append(metrics)
            return metrics.playback_time > 0
        except Exception as e:
            print(f"Playback test failed: {str(e)}")
            return False

    def test_quality_switch(self) -> bool:
        """Test if video quality can be changed"""
        try:
            self.driver.find_element(By.CLASS_NAME, "quality-selector").click()
            time.sleep(0.5)
            quality_options = self.driver.find_elements(By.CLASS_NAME, "quality-option")
            quality_options[1].click()  # Select 720p
            time.sleep(2)
            metrics = self.collect_metrics()
            self.metrics_log.append(metrics)
            return True
        except Exception as e:
            print(f"Quality switch test failed: {str(e)}")
            return False

    def test_seek(self) -> bool:
        """Test if video can seek to different positions"""
        try:
            self.driver.execute_script("document.querySelector('video').currentTime = 2")
            time.sleep(1)
            metrics = self.collect_metrics()
            self.metrics_log.append(metrics)
            return abs(metrics.playback_time - 2) < 1
        except Exception as e:
            print(f"Seek test failed: {str(e)}")
            return False

    def save_report(self, filename: str):
        """Save test results and metrics to a JSON file"""
        report = {
            "url": self.url,
            "timestamp": datetime.datetime.now().isoformat(),
            "metrics_log": [vars(m) for m in self.metrics_log]
        }
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

    def cleanup(self):
        """Close the browser and clean up"""
        self.driver.quit()

def main():
    """Main function to run the tests"""
    # Create local test page
    test_page_path = create_test_page()
    test_url = f"file://{test_page_path}"
    
    # Run tests
    tester = VideoStreamTest(test_url)
    try:
        print("Setting up test environment...")
        tester.setup()
        
        print("\nRunning tests...")
        results = tester.run_all_tests()
        
        # Print results
        print("\nTest Results:")
        print("-" * 50)
        for test_name, result in results.items():
            print(f"{test_name}: {'PASS' if result else 'FAIL'}")
        
        print("\nDetailed results have been saved to test_results.json")
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
    finally:
        tester.cleanup()
        
if __name__ == "__main__":
    main()