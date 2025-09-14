import { useEffect, useState } from "react";
import styles from "./VoiceWave.module.css";

type VoiceWaveProps = {
  isRecording: boolean;
  audioContext?: AudioContext;
  analyser?: AnalyserNode;
};

export default function VoiceWave({ isRecording, audioContext, analyser }: VoiceWaveProps) {
  const [waveData, setWaveData] = useState<number[]>([]);

  useEffect(() => {
    if (!isRecording || !analyser) return;

    const dataArray = new Uint8Array(analyser.frequencyBinCount);
    let animationId: number;

    const updateWave = () => {
      analyser.getByteFrequencyData(dataArray);
      
      // Convert to normalized values (0-1) and take every 4th value for performance
      const normalizedData = Array.from(dataArray)
        .filter((_, index) => index % 4 === 0)
        .slice(0, 20) // Limit to 20 bars
        .map(value => value / 255);
      
      setWaveData(normalizedData);
      animationId = requestAnimationFrame(updateWave);
    };

    updateWave();

    return () => {
      if (animationId) {
        cancelAnimationFrame(animationId);
      }
    };
  }, [isRecording, analyser]);

  if (!isRecording) return null;

  return (
    <div className={styles.waveContainer}>
      {waveData.length > 0 ? (
        <div className={styles.waveBars}>
          {waveData.map((height, index) => (
            <div
              key={index}
              className={styles.waveBar}
              style={{
                height: `${Math.max(height * 100, 5)}%`,
                animationDelay: `${index * 0.05}s`
              }}
            />
          ))}
        </div>
      ) : (
        <div className={styles.wavePlaceholder}>
          <div className={styles.waveBar} />
          <div className={styles.waveBar} />
          <div className={styles.waveBar} />
          <div className={styles.waveBar} />
          <div className={styles.waveBar} />
        </div>
      )}
    </div>
  );
}
