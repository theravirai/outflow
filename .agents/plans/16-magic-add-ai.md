# Plan: Voice Add Feature Implementation (Option 2 - Groq Whisper)

We will upgrade the "Magic Add" feature to a "Voice Add" feature. Instead of typing an expense, the user will record their voice. The frontend will send the audio to the backend, which will use Groq's `whisper-large-v3` to transcribe the speech to text, and then use an LLM (`llama3-8b-8192`) to extract structured JSON.

### 1. Update Dependencies
- **Task:** Ensure `groq` Python package is in `requirements.txt`. (Already installed in the virtual environment).

### 2. Frontend UI (`add_expense.html` & `expense.css`)
- **Task:** Update the Magic Add HTML block. Replace the text input and Auto-Fill button with a prominent "Microphone" button (using Lucide icons like `mic`).
- **Task:** Add styling for recording states (e.g., a pulsating red animation when actively recording) and a loading state ("Processing...").

### 3. Frontend Logic (`add_expense.html` JS)
- **Task:** Use the browser's native `MediaRecorder` API to capture audio from the user's microphone.
- **Logic:**
  1. On click/hold, request microphone permissions and start recording.
  2. Provide visual feedback (pulsating mic).
  3. On stop, collect the audio chunks into a `Blob` (e.g., `audio/webm`).
  4. Send the Blob to the backend via a `fetch` POST request using `FormData` (e.g., `formData.append('audio', blob, 'expense.webm')`).
  5. Wait for the JSON response and populate the form fields (`#amount`, `#category`, `#date`, `#description`).

### 4. Backend Implementation (`app.py`)
- **Task:** Create a new route `POST /api/magic-voice`.
- **Logic:**
  1. Receive the audio file from `request.files['audio']`.
  2. Use Groq's Audio API (`client.audio.transcriptions.create(model="whisper-large-v3", file=...)`) to convert the audio into raw text.
  3. Get today's date using `datetime.date.today().isoformat()`.
  4. Create a **System Prompt** instructing the AI to act as a financial data extractor (identical to the text-based Magic Add prompt).
  5. Call the Groq Chat API (`llama3-8b-8192`) with `response_format={"type": "json_object"}` to parse the transcribed text into JSON.
  6. Return the extracted `amount`, `category`, `date`, `description`, and optionally the raw `transcript` to the frontend.
