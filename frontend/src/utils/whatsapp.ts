/**
 * WhatsApp click-to-chat utility using number_to_whatsapp_link.py logic.
 * Default country code: 91 (India)
 */

export function makeWhatsAppLink(number?: string | null, countryCode: string = "91"): string | null {
  if (!number) return null;
  const digits = number.replace(/\D/g, "").trim();
  if (!digits) return null;

  let internationalNumber = digits;
  // If the number starts with the selected country code, keep it.
  // Otherwise, remove a leading local trunk zero and add the country code.
  if (digits.startsWith(countryCode) && digits.length > countryCode.length + 7) {
    internationalNumber = digits;
  } else {
    const stripped = digits.replace(/^0+/, "");
    internationalNumber = countryCode + stripped;
  }

  return `https://wa.me/${internationalNumber}`;
}

export const OFFICIAL_COMPLAINTS_WHATSAPP = "https://wa.me/919746603975";

export function getComplaintWhatsAppLink(match?: {
  id?: number | null;
  match_number?: number | null;
  team_a_name?: string | null;
  team_b_name?: string | null;
}): string {
  if (!match) return OFFICIAL_COMPLAINTS_WHATSAPP;
  const mNum = match.match_number || match.id || "";
  const matchDesc = mNum ? `Match #${mNum}` : "my fixture";
  const teamsDesc = match.team_a_name && match.team_b_name ? ` (${match.team_a_name} vs ${match.team_b_name})` : "";
  const message = `Hello Minaram Cup Admin, I would like to raise a complaint / submit walkover proof regarding ${matchDesc}${teamsDesc}.`;
  return `${OFFICIAL_COMPLAINTS_WHATSAPP}?text=${encodeURIComponent(message)}`;
}
