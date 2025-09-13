import { useEffect, useRef, useState } from "react";
import styles from "./SearchOverlay.module.css";

type SearchOverlayProps = {
  isOpen: boolean;
  onClose: () => void;
  onSearch: (query: string) => Promise<void>;
};

export default function SearchOverlay({ isOpen, onClose, onSearch }: SearchOverlayProps) {
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        cancelSearch();
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      return () => document.removeEventListener("keydown", handleEscape);
    }
  }, [isOpen, onClose]);

  const cancelSearch = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    setIsLoading(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
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

  // cleanup timeout on unmount or when closing
    useEffect(() => {
        if (!isOpen) {
        cancelSearch();
        setQuery(""); // clear query on close
        }
    }, [isOpen]);

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
              placeholder="Search events..."
              className={styles.input}
              disabled={isLoading}
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
        <div className={styles.hint}>
          Enter to search • Esc to close
        </div>
      </div>
    </div>
  );
}
