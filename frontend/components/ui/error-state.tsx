export function ErrorState({ message }: { message: string }) {
  return (
    <p className="rounded-xl border border-danger/20 bg-danger/5 px-4 py-3 text-sm text-danger" role="alert">
      {message}
    </p>
  );
}