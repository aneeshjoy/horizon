export function Footer() {
  return (
    <footer className="w-full border-t py-6 md:py-0">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 flex flex-col items-center justify-between gap-4 md:h-16 md:flex-row">
        <p className="text-center text-sm leading-loose text-muted-foreground md:text-left">
          Built with <span className="font-semibold">FastAPI</span> &{' '}
          <span className="font-semibold">React</span>. Source code available on{' '}
          <a
            href="https://github.com/yourusername/horizon"
            target="_blank"
            rel="noreferrer"
            className="font-medium underline underline-offset-4"
          >
            GitHub
          </a>
          .
        </p>
      </div>
    </footer>
  )
}
