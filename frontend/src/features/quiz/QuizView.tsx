import { BrainCircuit } from 'lucide-react';

export default function QuizView() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-white/40 gap-4">
      <BrainCircuit size={48} strokeWidth={1} />
      <h2 className="text-sm uppercase tracking-[0.3em]">Quiz & Flashcards</h2>
      <p className="text-xs text-white/25 max-w-sm text-center">
        Create quizzes and flashcards based on your explored topics to reinforce learning.
      </p>
    </div>
  );
}
