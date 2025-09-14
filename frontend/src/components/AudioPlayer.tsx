import { useRef, useEffect, useState } from "react"

type AudioPlayerWithVisualizerProps = {
  audioDataUrl: string // e.g. "data:audio/wav;base64,..."
}

export function AudioPlayerWithVisualizer({ audioDataUrl }: AudioPlayerWithVisualizerProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [isStopped, setIsStopped] = useState(true)
  const animationRef = useRef<number | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const audioCtxRef = useRef<AudioContext | null>(null)
  const sourceRef = useRef<MediaElementAudioSourceNode | null>(null)

  // Autoplay on mount
  useEffect(() => {
    handlePlayPause().catch(() => {
      // Autoplay might fail due to browser policies; ignore silently
    })
  }, [])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext("2d")
    if (!ctx) return

    const draw = () => {
      if (!analyserRef.current || !ctx) return
      const analyser = analyserRef.current
      const bufferLength = analyser.frequencyBinCount
      const dataArray = new Uint8Array(bufferLength)
      analyser.getByteFrequencyData(dataArray)

      ctx.clearRect(0, 0, canvas.width, canvas.height)

      const barWidth = 4
      const gap = 2
      const bars = Math.floor(canvas.width / (barWidth + gap))

      for (let i = 0; i < bars; i++) {
        const value = dataArray[i]
        const percent = value / 255
        const height = percent * canvas.height
        const offset = canvas.height - height
        const hue = 260 + percent * 100 // purple-blue Siri feel

        ctx.fillStyle = `hsl(${hue}, 80%, 60%)`
        ctx.fillRect(i * (barWidth + gap), offset, barWidth, height)
      }

      animationRef.current = requestAnimationFrame(draw)
    }

    if (isPlaying) {
      draw()
    } else {
      if (animationRef.current) cancelAnimationFrame(animationRef.current)
      ctx.clearRect(0, 0, canvas.width, canvas.height)
    }

    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current)
    }
  }, [isPlaying])

  const setupAudioContext = () => {
    if (!audioRef.current) return
    if (!audioCtxRef.current) {
      audioCtxRef.current = new AudioContext()
      sourceRef.current = audioCtxRef.current.createMediaElementSource(audioRef.current)
      analyserRef.current = audioCtxRef.current.createAnalyser()
      analyserRef.current.fftSize = 256
      sourceRef.current.connect(analyserRef.current)
      analyserRef.current.connect(audioCtxRef.current.destination)
    }
  }

  const handlePlayPause = async () => {
    const audio = audioRef.current
    if (!audio) return

    setupAudioContext()

    if (isPlaying) {
      audio.pause()
      setIsPlaying(false)
    } else {
      if (isStopped) {
        audio.currentTime = 0
        setIsStopped(false)
      }
      await audioCtxRef.current?.resume()
      audio.play().catch(() => {
        // Autoplay might fail; ignore silently
      })
      setIsPlaying(true)
    }
  }

  const handleStop = () => {
    const audio = audioRef.current
    if (!audio) return
    audio.pause()
    audio.currentTime = 0
    setIsPlaying(false)
    setIsStopped(true)
  }

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50">
      <div className="bg-white dark:bg-neutral-900 border border-neutral-300 dark:border-neutral-700 rounded-[60px] shadow-lg px-8 py-4 w-[90vw] max-w-xl flex items-center">
        {/* Hidden audio element */}
        <audio ref={audioRef} src={audioDataUrl} preload="auto" />

        {/* Siri-style visualizer */}
        <canvas ref={canvasRef} width={600} height={100} className="w-3/4 h-12 rounded-2xl bg-black" />

        {/* Controls */}
        <div className="flex space-x-3 ml-auto">
          {/* Play / Pause button */}
          <div
            role="button"
            onClick={handlePlayPause}
            className="w-12 h-12 flex items-center justify-center rounded-[60px] bg-white border border-zinc-400 shadow-sm text-black"
          >
            {isPlaying ? (
              <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                <rect x="6" y="4" width="4" height="16" rx="1" />
                <rect x="14" y="4" width="4" height="16" rx="1" />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M5 3v18l15-9-15-9z" />
              </svg>
            )}
          </div>

          {/* Stop button */}
          <div
            role="button"
            onClick={handleStop}
            className="w-12 h-12 flex items-center justify-center rounded-[999px] bg-red-600 hover:bg-red-700 text-white disabled:opacity-50"
            aria-disabled={isStopped}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
              <rect x="6" y="6" width="12" height="12" rx="1" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  )
}
