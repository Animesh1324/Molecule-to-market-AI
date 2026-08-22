'use client';

import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { CurrencyDisplay, getCurrencyPreference, setCurrencyPreference } from '../lib/currency';

interface CurrencyContextValue {
  display: CurrencyDisplay;
  setDisplay: (d: CurrencyDisplay) => void;
  ready: boolean;
}

const CurrencyContext = createContext<CurrencyContextValue>({
  display: 'inr-cr',
  setDisplay: () => undefined,
  ready: false,
});

export function CurrencyProvider({ children }: { children: React.ReactNode }) {
  // Start on the same default every server render produces, then reconcile
  // with the stored preference on mount — same hydration-safety pattern as
  // ThemeProvider.
  const [display, setDisplayState] = useState<CurrencyDisplay>('inr-cr');
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setDisplayState(getCurrencyPreference());
    setReady(true);
  }, []);

  const setDisplay = useCallback((d: CurrencyDisplay) => {
    setDisplayState(d);
    setCurrencyPreference(d);
  }, []);

  return (
    <CurrencyContext.Provider value={{ display, setDisplay, ready }}>
      {children}
    </CurrencyContext.Provider>
  );
}

export const useCurrency = () => useContext(CurrencyContext);
