import { toPng } from 'html-to-image';

/**
 * Downloads the tournament knockout bracket element as a high-resolution PNG graphic.
 * Captures the playoff structure and standings with official Minaram Cup branding.
 */
export async function downloadBracketAsPng(element: HTMLElement): Promise<void> {
  if (!element) {
    throw new Error('Target element not found for Bracket export');
  }

  // Ensure web fonts are ready before snapshot
  if (typeof document !== 'undefined' && 'fonts' in document) {
    try {
      await document.fonts.ready;
    } catch {
      // Graceful fallback
    }
  }

  const filename = `MinaramCup_Knockout_Bracket_${new Date().toISOString().slice(0, 10)}.png`;

  const captureOptions = {
    cacheBust: true,
    pixelRatio: 2.5,
    backgroundColor: '#0c0c0c',
    filter: (node: Node) => {
      if (node instanceof HTMLElement && node.dataset.exportHide === 'true') {
        return false;
      }
      return true;
    },
    style: {
      transform: 'none',
      boxShadow: 'none',
    },
  };

  let dataUrl: string;
  try {
    dataUrl = await toPng(element, captureOptions);
  } catch (err) {
    console.warn('Initial toPng failed for Bracket, retrying with local font styles:', err);
    dataUrl = await toPng(element, { ...captureOptions, fontEmbedCSS: '' });
  }

  const link = document.createElement('a');
  link.download = filename;
  link.href = dataUrl;
  link.style.display = 'none';
  document.body.appendChild(link);
  link.click();
  setTimeout(() => {
    document.body.removeChild(link);
  }, 150);
}
