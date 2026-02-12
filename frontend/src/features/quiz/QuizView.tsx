import { BrainCircuit } from 'lucide-react';

export default function QuizView() {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-5">
      <div className="p-5 rounded-2xl bg-accent-subtle">
        <BrainCircuit size={40} strokeWidth={1.2} className="text-accent" />
      </div>
      <div className="text-center space-y-2">
        <h2 className="text-base font-semibold text-text">Quiz & Flashcards</h2>
        <p className="text-sm text-text-tertiary max-w-md leading-relaxed">
          Create quizzes and flashcards based on your explored topics to reinforce learning through spaced repetition.
        </p>
      </div>
      <span className="text-xxs font-medium text-accent bg-accent-subtle px-3 py-1.5 rounded-lg">
        Coming soon
      </span>
    </div>
  );
}
