import type { ReactNode } from "react";

export default function HomePage(): ReactNode {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center">
      <h1 className="text-4xl font-bold">EchoSphere</h1>
      <p className="mt-4 text-lg text-gray-600">Real-time AI voice interaction platform</p>
    </main>
  );
}
