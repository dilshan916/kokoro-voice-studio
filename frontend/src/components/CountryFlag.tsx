import React from 'react';

interface CountryFlagProps {
  lang?: string;
  className?: string;
  alt?: string;
}

const FLAG_MAP: Record<string, string> = {
  'en-us': '/flags/us.svg',
  'us': '/flags/us.svg',
  '🇺🇸': '/flags/us.svg',

  'en-gb': '/flags/gb.svg',
  'gb': '/flags/gb.svg',
  'uk': '/flags/gb.svg',
  '🇬🇧': '/flags/gb.svg',

  'fr-fr': '/flags/fr.svg',
  'fr': '/flags/fr.svg',
  '🇫🇷': '/flags/fr.svg',

  'ja': '/flags/jp.svg',
  'jp': '/flags/jp.svg',
  '🇯🇵': '/flags/jp.svg',

  'ko': '/flags/kr.svg',
  'kr': '/flags/kr.svg',
  '🇰🇷': '/flags/kr.svg',

  'cmn': '/flags/cn.svg',
  'cn': '/flags/cn.svg',
  'zh': '/flags/cn.svg',
  '🇨🇳': '/flags/cn.svg',

  'es': '/flags/es.svg',
  '🇪🇸': '/flags/es.svg',

  'hi': '/flags/in.svg',
  'in': '/flags/in.svg',
  '🇮🇳': '/flags/in.svg',

  'it': '/flags/it.svg',
  '🇮🇹': '/flags/it.svg',

  'pt-br': '/flags/br.svg',
  'br': '/flags/br.svg',
  '🇧🇷': '/flags/br.svg',

  'all': '/flags/un.svg',
  'auto': '/flags/un.svg',
  '🌐': '/flags/un.svg',
};

export const CountryFlag: React.FC<CountryFlagProps> = ({
  lang = 'all',
  className = 'w-6 h-6 rounded-full object-cover shadow-sm shrink-0',
  alt,
}) => {
  const normalized = (lang || '').toLowerCase().trim();
  const src = FLAG_MAP[normalized] || FLAG_MAP[lang] || '/flags/un.svg';

  return (
    <img
      src={src}
      alt={alt || lang}
      className={className}
      loading="eager"
      decoding="async"
    />
  );
};

export default CountryFlag;
