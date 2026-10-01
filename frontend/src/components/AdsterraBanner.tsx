import React, { useEffect, useRef } from 'react';

export const AdsterraBanner: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Create and append the Adsterra native banner script
    const script = document.createElement('script');
    script.async = true;
    script.setAttribute('data-cfasync', 'false');
    script.src = 'https://bauval.org/21/b1b5ddc2fcb6edae958dd257079a2cb3';

    containerRef.current.appendChild(script);

    return () => {
      if (containerRef.current) {
        containerRef.current.innerHTML = '';
      }
    };
  }, []);

  return (
    <div className="w-full max-w-4xl mx-auto my-6 flex flex-col items-center justify-center overflow-hidden">
      <div
        id="container-b1b5ddc2fcb6edae958dd257079a2cb3"
        ref={containerRef}
        className="w-full flex justify-center items-center min-h-[90px]"
      />
    </div>
  );
};

export default AdsterraBanner;
