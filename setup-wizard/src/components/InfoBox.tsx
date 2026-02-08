interface InfoBoxProps {
  variant: 'why' | 'alternative' | 'explanation';
  title: string;
  children: React.ReactNode;
}

export function InfoBox({ variant, title, children }: InfoBoxProps) {
  const cls = `info-box info-${variant}`;

  return (
    <div className={cls}>
      <h4>{title}</h4>
      {typeof children === 'string' ? <p>{children}</p> : children}
    </div>
  );
}
