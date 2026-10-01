import React, { useRef, useEffect } from 'react';

export const AdsterraMobileBanner: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Create an isolated iframe to safely execute atOptions and external script
    const iframe = document.createElement('iframe');
    iframe.width = '320';
    iframe.height = '50';
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
              'key' : '01b74a850ca5aa141f384ddf31b7379c',
              'format' : 'iframe',
              'height' : 50,
              'width' : 320,
              'params' : {}
            };
          </script>
          <script type="text/javascript" src="https://bauval.org/22/01b74a850ca5aa141f384ddf31b7379c"></script>
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
    <div className="w-full flex justify-center items-center my-4 overflow-hidden">
      <div
        ref={containerRef}
        className="w-[320px] h-[50px] min-w-[320px] flex items-center justify-center bg-slate-100/50 dark:bg-slate-800/30 rounded-lg overflow-hidden"
      />
    </div>
  );
};

export default AdsterraMobileBanner;
