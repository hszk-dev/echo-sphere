import { PlaybackView } from "@/features/recording-player";
import Link from "next/link";

interface PlaybackPageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: PlaybackPageProps) {
  const { id } = await params;
  return {
    title: `Recording ${id.slice(-8)} | EchoSphere`,
    description: "Playback your voice conversation recording with synchronized transcript",
  };
}

export default async function PlaybackPage({ params }: PlaybackPageProps) {
  const { id } = await params;

  return (
    <div className="min-h-screen bg-background noise-texture">
      {/* Background atmosphere */}
      <div className="fixed inset-0 gradient-mesh pointer-events-none" aria-hidden="true" />
      <div className="fixed inset-0 bg-radial-subtle pointer-events-none" aria-hidden="true" />

      {/* Header */}
      <header className="border-b border-border/50 bg-surface/70 backdrop-blur-md sticky top-0 z-20">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="text-xl font-display font-bold text-primary hover:opacity-80 transition-opacity"
            >
              EchoSphere
            </Link>
            <span className="text-muted/50">/</span>
            <Link
              href="/recordings"
              className="text-foreground hover:text-primary transition-colors duration-200"
            >
              Recordings
            </Link>
            <span className="text-muted/50">/</span>
            <span className="text-muted">Playback</span>
          </div>
          <Link
            href="/"
            className="group px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium
                       hover:bg-primary/90 hover:shadow-glow transition-all duration-300 ease-out-expo"
          >
            <span className="flex items-center gap-2">
              <svg
                className="w-4 h-4 transition-transform duration-300 group-hover:rotate-90"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 4v16m8-8H4"
                />
              </svg>
              New Session
            </span>
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-10 container mx-auto px-4 py-8 page-enter">
        <PlaybackView recordingId={id} />
      </main>
    </div>
  );
}
