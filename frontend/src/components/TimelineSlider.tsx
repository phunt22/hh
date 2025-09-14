import { useState, useEffect } from "react"
import { Slider } from "@/components/ui/slider"

interface TimelineSliderProps {
  minIndex: number
  maxIndex: number
  value: number
  onChange: (value: number) => void
}

export default function TimelineSlider({
  minIndex,
  maxIndex,
  value,
  onChange,
}: TimelineSliderProps) {
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    // Trigger enter animation
    const timer = setTimeout(() => setIsVisible(true), 50)
    return () => clearTimeout(timer)
  }, [])

  return (
    <div
      className={`fixed bottom-6 left-1/2 -translate-x-1/2 z-50
        transition-all duration-500 ease-out
        ${isVisible ? "translate-y-0 opacity-100" : "translate-y-10 opacity-0"}`}
    >
      <div className="bg-white dark:bg-neutral-900 border border-neutral-300 dark:border-neutral-700 rounded-2xl shadow-lg px-6 py-4 w-[90vw] max-w-xl">
        <Slider
          min={minIndex}
          max={maxIndex}
          step={1}
          value={[value]}
          onValueChange={(val) => onChange(val[0])}
          className="w-full"
        />
      </div>
    </div>
  )
}
