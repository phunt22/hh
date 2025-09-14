import { useQuery } from '@tanstack/react-query';
import { GoogleGenAI } from '@google/genai';

interface Event {
    title: string;
    description: string;
    date: string;
}

interface UseEventInsightsParams {
    event: Event;
    enabled: boolean;
}
const ai = new GoogleGenAI({
  apiKey: import.meta.env.VITE_GEMINI_API_KEY,
});


export function useEventInsights({ event, enabled }: UseEventInsightsParams) {
  
    const { data, isLoading, isError } = useQuery({
        queryKey: ['eventInsights', event],
        queryFn: async () => {
            const response = await ai.models.generateContent({
                model: 'gemini-2.5-flash',
                contents: [
                    { text: `Event: ${event.title} - ${event.description} on ${event.date}` },
                    { text: 'What are people saying about this event and what is it about?' },
                    { text: "Return data as plain text and not markdown" }
                ],
                config: {
                    tools: [{ googleSearch: {} }],
                },
            });

            return response.text ?? "";
        },
        enabled,
    });
    return { data, isLoading, isError };
}