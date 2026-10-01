import React, { useRef, useEffect } from 'react';

export const AdsterraLeaderboard: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Create an isolated iframe to safely execute atOptions and external script
    const iframe = document.createElement('iframe');
    iframe.width = '728';
    iframe.height = '90';
    iframe.frameBorder = '0';
    iframe.scrolling = 'no';
    iframe.style.border = 'none';
    iframe.style.overflow = 'hidden';
    iframe.title = 'Advertisement';

    const htmlContent = `
      <!DOCTYPE html>
      <html>
        <head>
          <base target="_blank">
          <style>
            body { margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; background: transparent; overflow: hidden; }
          </style>
        </head>
        <body>
          <script type="text/javascript">
            atOptions = {
              'key' : 'e0e0fdad532cda490402ef24996fc64b',
              'format' : 'iframe',
              'height' : 90,
              'width' : 728,
              'params' : {}
            };
          </script>
          <script type="text/javascript" src="https://bauval.org/22/e0e0fdad532cda490402ef24996fc64b"></script>
        </body>
      </html>
    `;

    iframe.srcdoc = htmlContent;
    containerRef.current.innerHTML = '';
    containerRef.current.appendChild(iframe);

    return () => {
      if (containerRef.current) {
        containerRef.current.innerHTML = '';
      }
    };
  }, []);

  return (
    <div className="w-full flex justify-center items-center my-6 overflow-x-auto">
      <div
        ref={containerRef}
        className="w-[728px] h-[90px] min-w-[728px] flex items-center justify-center bg-slate-100/50 dark:bg-slate-800/30 rounded-xl overflow-hidden"
      />
    </div>
  );
};

export default AdsterraLeaderboard;
