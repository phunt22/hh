import { useEffect, useRef, useState } from "react";
import styles from "./SearchOverlay.module.css";
import MicrophoneIcon from "./MicrophoneIcon";
import SpeakerIcon from "./SpeakerIcon";
import VoiceWave from "./VoiceWave";
import { EventsAPI } from "../services/api";

type SearchOverlayProps = {
  isOpen: boolean;
  onClose: () => void;
  onSearch: (query: string) => Promise<void>;
};

export default function SearchOverlay({ isOpen, onClose, onSearch }: SearchOverlayProps) {
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isDictating, setIsDictating] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        cancelSearch();
        onClose();
      } else if (e.key === "Enter") {
        if (isRecording || isDictating) {
          // Stop voice operations and submit immediately
          e.preventDefault();
          if (isRecording) {
            if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
              mediaRecorderRef.current.stop();
            }
            if (audioContextRef.current) {
              audioContextRef.current.close();
              audioContextRef.current = null;
              analyserRef.current = null;
            }
            setIsRecording(false);
          }
          if (isDictating) {
            if (recognitionRef.current) {
              recognitionRef.current.stop();
            }
            setIsDictating(false);
          }
          // Submit the form immediately after stopping
          if (query.trim() && !isLoading) {
            handleSubmit(e as any);
          }
        }
        // If not recording/dictating, let the form handle Enter normally
      }
    };

    if (isOpen) {
      document.addEventListener("keydown", handleKeyDown);
      return () => document.removeEventListener("keydown", handleKeyDown);
    }
  }, [isOpen, onClose, isRecording, isDictating, query, isLoading]);

  const cancelSearch = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    setIsLoading(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Only stop voice operations if they're still running
    // (This prevents double-stopping when Enter is pressed during voice modes)
    if (isRecording) {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
        audioContextRef.current = null;
        analyserRef.current = null;
      }
      setIsRecording(false);
    }
    
    if (isDictating) {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      setIsDictating(false);
    }
    
    if (query.trim() && !isLoading) {
      setIsLoading(true);
      try {
        await onSearch(query.trim());
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      cancelSearch();
      onClose();
    }
  };

  const handleVoiceRecord = async () => {
    if (isRecording) {
      // Stop recording
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
        audioContextRef.current = null;
        analyserRef.current = null;
      }
      setIsRecording(false);
    } else {
      // Stop dictation if it's running
      if (isDictating) {
        if (recognitionRef.current) {
          recognitionRef.current.stop();
        }
        setIsDictating(false);
      }
      
      // Start recording
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        // Set up audio context for wave visualization
        const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
        const analyser = audioContext.createAnalyser();
        const source = audioContext.createMediaStreamSource(stream);
        
        analyser.fftSize = 256;
        source.connect(analyser);
        
        audioContextRef.current = audioContext;
        analyserRef.current = analyser;
        
        // Set up media recorder
        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorderRef.current = mediaRecorder;
        
        const audioChunks: Blob[] = [];
        
        mediaRecorder.ondataavailable = (event) => {
          audioChunks.push(event.data);
        };
        
        mediaRecorder.onstop = async () => {
          const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
          try {
            // Send audio to backend for STT processing
            const result = await EventsAPI.transcribeAudio(audioBlob);
            setQuery(prev => prev + (prev ? " " : "") + result.text);
          } catch (error) {
            console.error('Error transcribing audio:', error);
            // Fallback to placeholder
            setQuery(prev => prev + (prev ? " " : "") + "[Voice recorded]");
          }
          
          // Clean up audio context
          if (audioContextRef.current) {
            audioContextRef.current.close();
            audioContextRef.current = null;
            analyserRef.current = null;
          }
        };
        
        mediaRecorder.start();
        setIsRecording(true);
      } catch (error) {
        console.error('Error accessing microphone:', error);
        // Handle error - maybe show a toast
      }
    }
  };

  const handleDictation = () => {
    if (isDictating) {
      // Stop dictation
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      setIsDictating(false);
    } else {
      // Stop recording if it's running
      if (isRecording) {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
          mediaRecorderRef.current.stop();
        }
        if (audioContextRef.current) {
          audioContextRef.current.close();
          audioContextRef.current = null;
          analyserRef.current = null;
        }
        setIsRecording(false);
      }
      
      // Start dictation
      if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        
        recognition.continuous = false; // Only process one phrase at a time
        recognition.interimResults = false; // Only use final results
        recognition.lang = 'en-US';
        recognition.maxAlternatives = 1; // Only get the best result
        
        recognition.onstart = () => {
          setIsDictating(true);
          // Clear the search box when starting fresh dictation
          setQuery("");
        };
        
        // Add timeout to stop dictation after 10 seconds of silence
        const timeoutId = setTimeout(() => {
          if (recognitionRef.current) {
            recognitionRef.current.stop();
          }
        }, 10000);
        
        recognition.onresult = (event: any) => {
          clearTimeout(timeoutId); // Clear timeout when we get a result
          
          let finalTranscript = '';
          
          for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
              finalTranscript += transcript;
            }
          }
          
          // Only update with final results to prevent loops
          if (finalTranscript.trim()) {
            setQuery(prev => {
              // Clear any previous interim text and add only the final transcript
              const cleanText = prev.replace(/\s*\[.*?\]\s*$/, '').trim();
              return cleanText + (cleanText ? ' ' : '') + finalTranscript.trim();
            });
          }
        };
        
        recognition.onerror = (event: any) => {
          clearTimeout(timeoutId);
          console.error('Speech recognition error:', event.error);
          setIsDictating(false);
        };
        
        recognition.onend = () => {
          clearTimeout(timeoutId);
          setIsDictating(false);
        };
        
        recognitionRef.current = recognition;
        recognition.start();
      } else {
        console.error('Speech recognition not supported');
        // Fallback: show a message or use a different approach
      }
    }
  };

  // cleanup timeout on unmount or when closing
    useEffect(() => {
        if (!isOpen) {
        cancelSearch();
        setQuery(""); // clear query on close
        
        // Stop any ongoing voice operations
        if (isRecording && mediaRecorderRef.current) {
          mediaRecorderRef.current.stop();
          setIsRecording(false);
        }
        if (isDictating && recognitionRef.current) {
          recognitionRef.current.stop();
          setIsDictating(false);
        }
        if (audioContextRef.current) {
          audioContextRef.current.close();
          audioContextRef.current = null;
          analyserRef.current = null;
        }
        }
    }, [isOpen, isRecording, isDictating]);

    // cleanup timeout on unmount
    useEffect(() => {
        return () => {
        if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
        }
        };
    }, []);

  if (!isOpen) return null;

  return (
    <div className={styles.backdrop} onClick={handleBackdropClick}>
      <div className={styles.container}>
        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={`${styles.inputWrapper} ${isLoading ? styles.loading : ""}`}>
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={isRecording ? "Recording..." : isDictating ? "Listening..." : "Search events..."}
              className={styles.input}
              disabled={isLoading}
            />
            <VoiceWave 
              isRecording={isRecording}
              audioContext={audioContextRef.current}
              analyser={analyserRef.current}
            />
            {isLoading && (
              <>
                <svg className={styles.borderSvg} viewBox="0 0 516 64" xmlns="http://www.w3.org/2000/svg">
                  <rect 
                    x="6" 
                    y="6" 
                    width="504" 
                    height="52" 
                    rx="18" 
                    ry="18" 
                    fill="none" 
                    stroke="rgba(255,255,255,1)" 
                    strokeWidth="4" 
                    strokeLinecap="round"
                    pathLength={1000}
                    className={styles.borderPath}
                  />
                </svg>
              </>
            )}
          </div>
        </form>
        <div className={styles.voiceButtons}>
          <MicrophoneIcon 
            onClick={handleVoiceRecord}
            disabled={isLoading || isDictating}
            isRecording={isRecording}
            title={isRecording ? "Stop Recording" : isDictating ? "Stop dictation first" : "Record Voice Message"}
          />
          <SpeakerIcon 
            onClick={handleDictation}
            disabled={isLoading || isRecording}
            isDictating={isDictating}
            title={isDictating ? "Stop Dictation" : isRecording ? "Stop recording first" : "Type as You Speak"}
          />
        </div>
        <div className={styles.hint}>
          {isRecording ? "Recording... Press Enter to stop and send immediately" : 
           isDictating ? "Listening... Press Enter to stop and send immediately" : 
           "Enter to search • Esc to close"}
        </div>
      </div>
    </div>
  );
}
