/**
 * CAT Parts Store URLs for 308E2 CR Mini Hydraulic Excavator.
 * Base: https://parts.cat.com/en/catcorp/category/electrical-electronics?filterByEquipment=true&model=308E2+CR
 */
const CAT_PARTS_BASE = 'https://parts.cat.com/en/catcorp';
const MODEL = '308E2 CR';

export function getPartSearchUrl(partNumber: string): string {
  const q = encodeURIComponent(partNumber.trim());
  const model = encodeURIComponent(MODEL);
  return `${CAT_PARTS_BASE}/search?q=${q}&filterByEquipment=true&model=${model}`;
}
