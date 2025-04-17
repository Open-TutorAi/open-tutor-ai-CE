import { browser } from '$app/environment';
import type { PageLoad } from './$types';

export const load: PageLoad = async () => {
  if (!browser) {
    return { props: {} };
  }
  
  return {
    props: {}
  };
}; 