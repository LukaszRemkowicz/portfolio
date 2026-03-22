import { createContext, useContext } from 'react';

export const RequestOriginContext = createContext<string | null>(null);

export function useRequestOrigin(): string | null {
  return useContext(RequestOriginContext);
}
