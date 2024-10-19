import android.app.Activity
import android.os.Bundle
import android.speech.tts.TextToSpeech
import android.util.Log
import org.opencv.android.CameraBridgeViewBase
import org.opencv.core.Mat
import java.util.*

class MainActivity : Activity(), CameraBridgeViewBase.CvCameraViewListener2, TextToSpeech.OnInitListener {

    private lateinit var tts: TextToSpeech
    private lateinit var openCvCameraView: CameraBridgeViewBase

    // Counter for detecting hand-up events
    private var leftHandCounter = 0
    private var rightHandCounter = 0
    private val throttle = 10

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Initialize OpenCV and TextToSpeech
        tts = TextToSpeech(this, this)
        openCvCameraView = findViewById(R.id.camera_view)  // assuming you have a CameraBridgeViewBase in your layout
        openCvCameraView.visibility = CameraBridgeViewBase.VISIBLE
        openCvCameraView.setCvCameraViewListener(this)
    }

    override fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) {
            tts.language = Locale.US
        } else {
            Log.e("TTS", "Initialization failed!")
        }
    }

    override fun onCameraFrame(inputFrame: CameraBridgeViewBase.CvCameraViewFrame): Mat {
        val frame = inputFrame.rgba()

        // Process the frame for hand detection (using MediaPipe or OpenCV)
        // Detect if the left or right hand is raised
        val (leftHandUp, rightHandUp) = detectHandAboveHead(frame)

        // Throttling logic for speech synthesis
        if (leftHandUp) {
            leftHandCounter++
            if (leftHandCounter % throttle == 0) {
                ttsSpeak("Left hand is up")
            }
        } else {
            leftHandCounter = 0
        }

        if (rightHandUp) {
            rightHandCounter++
            if (rightHandCounter % throttle == 0) {
                ttsSpeak("Right hand is up")
            }
        } else {
            rightHandCounter = 0
        }

        // Return the processed frame to be displayed
        return frame
    }

    private fun detectHandAboveHead(frame: Mat): Pair<Boolean, Boolean> {
        // Implement your hand detection logic here
        // Use MediaPipe or OpenCV to detect hand position in the frame
        // Return a pair of booleans indicating if left or right hand is above the head
        return Pair(false, false)
    }

    private fun ttsSpeak(text: String) {
        tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, null)
    }

    override fun onDestroy() {
        // Shutdown the TTS when activity is destroyed
        if (tts != null) {
            tts.stop()
            tts.shutdown()
        }
        super.onDestroy()
    }
}

