import { toPng } from 'html-to-image';
import { PublicMatch } from '../types';

/**
 * Downloads a MatchCard element as a high-resolution PNG image.
 * Matches the tournament design aesthetic with dark background and crisp typography.
 */
export async function downloadMatchCardAsPng(
  element: HTMLElement,
  match: PublicMatch
): Promise<void> {
  if (!element) {
    throw new Error('Target element not found for PNG export');
  }

  // Ensure browser fonts are fully rendered before capturing snapshot
  if (typeof document !== 'undefined' && 'fonts' in document) {
    try {
      await document.fonts.ready;
    } catch {
      // Graceful fallback if fonts API unavailable
    }
  }

  // Generate clean, descriptive filename
  const clean = (val?: string | null) =>
    (val || 'TBD')
      .trim()
      .replace(/[^a-zA-Z0-9_-]/g, '_')
      .replace(/_+/g, '_');

  const matchLabel = match.match_number ? `M#${match.match_number}` : `Match_${match.id || 'Fixture'}`;
  const teamA = clean(match.team_a_name);
  const teamB = clean(match.team_b_name);
  const stage = clean(match.stage || 'Match');
  const filename = `MinaramCup_${matchLabel}_${teamA}_vs_${teamB}.png`;

  const captureOptions = {
    cacheBust: true,
    pixelRatio: 2.5,
    backgroundColor: '#121212',
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
    console.warn('Initial toPng failed, retrying with local font styles:', err);
    // Fallback skipping external font embed CSS to avoid CORS stylesheet restrictions
    dataUrl = await toPng(element, { ...captureOptions, fontEmbedCSS: '' });
  }

  // Trigger browser file download
  const link = document.createElement('a');
  link.download = filename;
  link.href = dataUrl;
  link.style.display = 'none';
  document.body.appendChild(link);
  link.click();
  setTimeout(() => {
    document.body.removeChild(link);
  }, 100);
}
