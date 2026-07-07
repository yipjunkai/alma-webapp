export default function HomePage() {
  return (
    <div className="flex min-h-svh flex-col bg-background">
      <header className="flex items-center px-6 py-4">
        <span className="text-sm font-semibold tracking-tight">Alma</span>
      </header>

      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col items-center justify-center gap-4 px-6 py-16 text-center">
        <h1 className="text-4xl font-semibold tracking-tight text-balance sm:text-5xl">
          Alma
        </h1>
        <p className="max-w-xl text-base text-pretty text-muted-foreground sm:text-lg">
          Immigration legal services — get an assessment of your case.
        </p>
      </main>
    </div>
  );
}
