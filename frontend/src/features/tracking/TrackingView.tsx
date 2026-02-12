import { TrendingDown } from 'lucide-react';

export default function TrackingView() {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-5">
      <div className="p-5 rounded-2xl bg-accent-subtle">
        <TrendingDown size={40} strokeWidth={1.2} className="text-accent" />
      </div>
      <div className="text-center space-y-2">
        <h2 className="text-base font-semibold text-text">Memory Tracking</h2>
        <p className="text-sm text-text-tertiary max-w-md leading-relaxed">
          Track explored topics and visualize the forgetting curve to review them at the optimal time.
        </p>
      </div>
      <span className="text-xxs font-medium text-accent bg-accent-subtle px-3 py-1.5 rounded-lg">
        Coming soon
      </span>
    </div>
  );
}
