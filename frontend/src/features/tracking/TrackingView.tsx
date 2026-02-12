import { TrendingDown } from 'lucide-react';

export default function TrackingView() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-white/40 gap-4">
      <TrendingDown size={48} strokeWidth={1} />
      <h2 className="text-sm uppercase tracking-[0.3em]">Memory Tracking</h2>
      <p className="text-xs text-white/25 max-w-sm text-center">
        Track explored topics and visualize the forgetting curve to review them at the optimal time.
      </p>
    </div>
  );
}
