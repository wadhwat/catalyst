import { ImageSourcePropType } from 'react-native';

const images: Record<string, ImageSourcePropType> = {
  cooling_system_hose: require('../../assets/demo/CoolingSystemHose.jpg'),
  damaged_access_ladder: require('../../assets/demo/DamagedAccessLadder.jpg'),
  hydraulic_fluid: require('../../assets/demo/HydraulicFluidFiltration.jpg'),
  rust_hydraulic: require('../../assets/demo/RustOnHydraulicComponentBracket.jpg'),
  structural_damage: require('../../assets/demo/StructuralDamage.jpg'),
  tire_wear: require('../../assets/demo/TireUnevenWear.jpg'),
};

const ITEM_TO_IMAGE: Record<string, string> = {
  'undercarriage': 'tire_wear',
  'cooling system': 'cooling_system_hose',
  'all hoses': 'cooling_system_hose',
  'radiator': 'cooling_system_hose',
  'steps & handholds': 'damaged_access_ladder',
  'hydraulic oil tank': 'hydraulic_fluid',
  'hydraulic oil filters': 'hydraulic_fluid',
  'hydraulic pilot oil filter': 'hydraulic_fluid',
  'hydraulic oil cooler': 'hydraulic_fluid',
  'bucket cylinder & linkage': 'rust_hydraulic',
  'boom, cylinders': 'rust_hydraulic',
  'stick, cylinder': 'rust_hydraulic',
  'carbody': 'structural_damage',
  'overall machine': 'structural_damage',
  'rops': 'structural_damage',
  'bucket/get': 'structural_damage',
  'overall engine compartment': 'structural_damage',
};

const keys = Object.keys(ITEM_TO_IMAGE);

export function getDemoImage(itemId: string): ImageSourcePropType | null {
  const lower = itemId.toLowerCase().replace(/_/g, ' ');
  const match = ITEM_TO_IMAGE[lower];
  if (match) return images[match];
  const partial = keys.find((k) => lower.includes(k) || k.includes(lower));
  if (partial) return images[ITEM_TO_IMAGE[partial]];
  return null;
}
