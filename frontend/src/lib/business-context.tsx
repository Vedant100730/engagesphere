"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";

const STORAGE_KEY = "engagesphere_business_id";

interface BusinessContextValue {
  businessId: string;
  setBusinessId: (id: string) => void;
}

const BusinessContext = createContext<BusinessContextValue>({
  businessId: "",
  setBusinessId: () => {},
});

export function BusinessProvider({ children }: { children: ReactNode }) {
  const [businessId, setBusinessIdState] = useState<string>("");

  // Load from sessionStorage on mount
  useEffect(() => {
    const stored = sessionStorage.getItem(STORAGE_KEY) ?? "";
    setBusinessIdState(stored);
  }, []);

  const setBusinessId = (id: string) => {
    sessionStorage.setItem(STORAGE_KEY, id);
    setBusinessIdState(id);
  };

  return (
    <BusinessContext.Provider value={{ businessId, setBusinessId }}>
      {children}
    </BusinessContext.Provider>
  );
}

export function useBusinessId() {
  return useContext(BusinessContext);
}
