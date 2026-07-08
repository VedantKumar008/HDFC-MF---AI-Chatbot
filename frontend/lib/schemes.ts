export interface Scheme {
  id: string;
  name: string;
  url: string;
}

export interface SchemeManifest {
  version: number;
  description: string;
  schemes: Scheme[];
}

export const APPROVED_SCHEME_COUNT = 21;

import schemeManifest from "./schemes-data.json";

export function getApprovedSchemes(): Scheme[] {
  return schemeManifest.schemes;
}

export { schemeManifest };
